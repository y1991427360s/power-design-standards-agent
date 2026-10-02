import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from config.settings import ROOT, FILES, SOURCE_TYPES, STANDARD_TYPES, TOP_K, ALLOW_EXTERNAL, ALLOWED_HOSTS
from database.store import init_db, connect
from backend.services import import_document, reparse, now
from agent.query import answer
from rag.search import search
from rag.embeddings import Embeddings

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title='电力设计规范智能查询 Agent',lifespan=lifespan)

@app.middleware('http')
async def local_protection(request: Request, call_next):
    # 公开部署必须在反向代理配置访问保护；默认仍仅供本机。
    host = request.headers.get('host','').split(':')[0].lower()
    if host not in ALLOWED_HOSTS:
        return JSONResponse({'detail':'访问域名未授权'},status_code=403)
    origin = request.headers.get('origin')
    if origin and origin not in (f'http://{request.headers.get("host")}',f'https://{request.headers.get("host")}'):
        return JSONResponse({'detail':'拒绝跨站请求'},status_code=403)
    return await call_next(request)

@app.exception_handler(Exception)
async def unhandled(request, exc):
    logging.exception('Request failed')
    return JSONResponse({'detail':'操作失败，请查看服务日志；资料不会被用于生成虚构条文。'},status_code=500)

class Query(BaseModel):
    question: str = Field(min_length=2,max_length=2000)
    document_ids: list[str] | None = None
    top_k: int = Field(default=TOP_K,ge=1,le=30)
    conversation_id: str | None = None
    category: str = ''
    source_types: list[str] | None = None

class Rule(BaseModel):
    title: str = Field(min_length=1,max_length=200)
    category: str = ''
    condition: str = ''
    rule: str = Field(min_length=1,max_length=10000)
    exceptions: str = ''
    source: str = ''

class Metadata(BaseModel):
    standard_name: str = Field(min_length=1,max_length=200)
    standard_code: str = ''
    version: str = ''
    publication_date: str = ''
    effective_date: str = ''
    source_type: str = 'STANDARD'
    standard_type: str = '其他'
    category: str = ''
    lifecycle: str = '现行'
    supersedes: str = ''

def validate_meta(meta):
    if meta['source_type'] not in SOURCE_TYPES: raise HTTPException(400,'资料类型无效')
    if meta['standard_type'] not in STANDARD_TYPES: raise HTTPException(400,'标准分类无效')
    if meta['lifecycle'] not in ('现行','废止','被替代','待核验'): raise HTTPException(400,'版本状态无效')

def document(document_id):
    with connect() as db:
        row = db.execute('SELECT * FROM documents WHERE document_id=?',(document_id,)).fetchone()
    if not row: raise HTTPException(404,'文档不存在')
    return dict(row)

@app.get('/api/settings')
def settings():
    return {'top_k':TOP_K,'allow_external_api':ALLOW_EXTERNAL,'embedding':Embeddings().identity,
            'llm_configured':bool(os.getenv('LLM_MODEL')),'source_types':SOURCE_TYPES,'standard_types':STANDARD_TYPES}

@app.get('/api/documents')
def documents():
    with connect() as db:
        return [dict(r) for r in db.execute('''SELECT d.*,COUNT(c.id) chunk_count FROM documents d
          LEFT JOIN clauses c ON d.document_id=c.document_id GROUP BY d.document_id ORDER BY d.created_at DESC''')]

@app.post('/api/documents')
async def upload(file: UploadFile = File(...), metadata: str = Form('{}')):
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in ('.pdf','.docx','.txt'): raise HTTPException(400,'仅支持 PDF、DOCX、TXT')
    try:
        meta = Metadata(**json.loads(metadata)).model_dump()
    except Exception:
        raise HTTPException(400,'文档信息不完整，请填写规范名称和有效元数据。')
    validate_meta(meta)
    path = FILES / (str(uuid4())+suffix)
    size = 0
    try:
        with path.open('wb') as output:
            while chunk := await file.read(1024*1024):
                size += len(chunk)
                if size > 50*1024*1024: raise HTTPException(413,'文件不得超过 50MB')
                output.write(chunk)
        if not size: raise HTTPException(400,'文件为空')
    except Exception:
        path.unlink(missing_ok=True)
        raise
    try:
        doc_id = await run_in_threadpool(import_document,path,meta,Path(file.filename).name)
        return document(doc_id)
    except Exception:
        raise HTTPException(422,'解析或索引失败，文档已保留在规范列表中；请查看状态说明，修复后重新解析。')

@app.get('/api/documents/{doc_id}')
def get_document(doc_id): return document(doc_id)

@app.patch('/api/documents/{doc_id}')
def update_document(doc_id, meta: Metadata):
    document(doc_id)
    values = meta.model_dump(); validate_meta(values)
    with connect() as db:
        db.execute(f'UPDATE documents SET {",".join(k+"=?" for k in values)} WHERE document_id=?',list(values.values())+[doc_id])
    return document(doc_id)

@app.delete('/api/documents/{doc_id}')
def delete_document(doc_id):
    doc = document(doc_id)
    # 仅删除本系统管理的文件。
    path = Path(doc['source_file']).resolve()
    if path.is_relative_to(FILES.resolve()): path.unlink(missing_ok=True)
    with connect() as db: db.execute('DELETE FROM documents WHERE document_id=?',(doc_id,))
    return {'ok':True}

@app.post('/api/documents/{doc_id}/reparse')
def parse_again(doc_id):
    document(doc_id)
    try: return {'chunk_count':reparse(doc_id)}
    except Exception: raise HTTPException(422,'重新解析失败，请查看文档状态说明。')

@app.get('/api/documents/{doc_id}/clauses')
def clauses(doc_id):
    document(doc_id)
    with connect() as db:
        return [dict(r) for r in db.execute('SELECT id,chapter,section,clause,title,text,page,page_end,page_kind,parse_quality FROM clauses WHERE document_id=? ORDER BY rowid',(doc_id,))]

@app.get('/api/clauses/{clause_id}')
def clause_context(clause_id):
    with connect() as db:
        row = db.execute('SELECT * FROM clauses WHERE id=?',(clause_id,)).fetchone()
        if not row: raise HTTPException(404,'条文不存在，可能已重新解析。')
        rows = [dict(r) for r in db.execute('SELECT id,clause,text,page,page_end FROM clauses WHERE document_id=? ORDER BY rowid',(row['document_id'],))]
    index = next(i for i,r in enumerate(rows) if r['id'] == clause_id)
    return {'clause':dict(row),'document':document(row['document_id']),'context':rows[max(0,index-1):index+2]}

@app.get('/api/documents/{doc_id}/file')
def original(doc_id):
    doc = document(doc_id)
    if not Path(doc['source_file']).exists(): raise HTTPException(404,'原始文件不存在')
    return FileResponse(doc['source_file'],filename=doc['filename'],content_disposition_type='inline')

@app.post('/api/search')
def search_test(query: Query):
    rows = search(query.question,document_ids=query.document_ids,top_k=query.top_k,
                  category=query.category,source_types=query.source_types)
    for row in rows: row.pop('vector',None)
    return rows

@app.post('/api/chat')
def chat(query: Query):
    result = answer(query.question,query.document_ids,query.top_k)
    # 不将 512 维索引向量写入聊天记录或前端。
    for row in result['citations']+result['references']: row.pop('vector',None)
    conversation_id = query.conversation_id or str(uuid4())
    with connect() as db:
        db.execute('INSERT OR IGNORE INTO conversations VALUES (?,?,?)',(conversation_id,query.question[:40],now()))
        db.execute('INSERT INTO messages(conversation_id,question,answer,created_at) VALUES (?,?,?,?)',
                   (conversation_id,query.question,json.dumps(result,ensure_ascii=False),now()))
    return {**result,'conversation_id':conversation_id}

@app.get('/api/conversations')
def conversations():
    with connect() as db: return [dict(r) for r in db.execute('SELECT * FROM conversations ORDER BY created_at DESC')]

@app.get('/api/conversations/{conversation_id}')
def conversation(conversation_id):
    with connect() as db:
        return [{**dict(r),'answer':json.loads(r['answer'])} for r in db.execute('SELECT * FROM messages WHERE conversation_id=? ORDER BY id',(conversation_id,))]

@app.get('/api/rules')
def rules():
    with connect() as db: return [dict(r) for r in db.execute('SELECT * FROM rules ORDER BY updated_at DESC')]

@app.post('/api/rules')
def create_rule(rule: Rule):
    rule_id = str(uuid4())
    with connect() as db: db.execute('INSERT INTO rules VALUES (?,?,?,?,?,?,?,?,?)',[rule_id]+list(rule.model_dump().values())+[now(),now()])
    return {'id':rule_id}

@app.put('/api/rules/{rule_id}')
def update_rule(rule_id, rule: Rule):
    with connect() as db:
        if not db.execute('SELECT id FROM rules WHERE id=?',(rule_id,)).fetchone(): raise HTTPException(404,'判据不存在')
        values = rule.model_dump()
        db.execute(f'UPDATE rules SET {",".join(k+"=?" for k in values)},updated_at=? WHERE id=?',list(values.values())+[now(),rule_id])
    return {'ok':True}

@app.delete('/api/rules/{rule_id}')
def delete_rule(rule_id):
    with connect() as db: db.execute('DELETE FROM rules WHERE id=?',(rule_id,))
    return {'ok':True}

app.mount('/',StaticFiles(directory=ROOT/'frontend',html=True),name='frontend')
