import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from database.store import connect
from parser.documents import parse
from rag.embeddings import Embeddings

def now(): return datetime.now(timezone.utc).isoformat()

def reparse(document_id):
    with connect() as db:
        doc = db.execute('SELECT * FROM documents WHERE document_id=?',(document_id,)).fetchone()
    if doc is None: raise ValueError('文档不存在')
    try:
        records, warning = parse(Path(doc['source_file']))
        embedding = Embeddings()
        vectors = []
        for start in range(0,len(records),32):
            vectors.extend(embedding.embed([r['text'] for r in records[start:start+32]]))
        with connect() as db:
            db.execute('DELETE FROM clauses WHERE document_id=?',(document_id,))
            for record, vector in zip(records,vectors):
                db.execute('INSERT INTO clauses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (str(uuid4()),document_id,record['chapter'],record['section'],record['clause'],record['title'],
                     record['text'],record['page'],record['page_end'],record['page_kind'],record['parse_quality'],
                     json.dumps(vector),embedding.identity))
            # DEMO 无法仅靠上传表单隐藏。
            demo = bool(doc['is_demo']) or 'DEMO' in (doc['standard_name']+' '+doc['standard_code']+' '+doc['filename']).upper() or any('DEMO' in r['text'].upper() or '非真实规范' in r['text'] for r in records)
            db.execute("UPDATE documents SET status='已就绪', warning=?, is_demo=? WHERE document_id=?",(warning,int(demo),document_id))
        return len(records)
    except Exception as exc:
        with connect() as db:
            db.execute("UPDATE documents SET status='解析失败',warning=? WHERE document_id=?",(str(exc)[:500],document_id))
        raise

def import_document(path, metadata, filename=None):
    document_id = str(uuid4())
    values = dict(filename=filename or path.name,standard_name=metadata.get('standard_name') or path.stem,
        standard_code='',version='',publication_date='',effective_date='',source_type='STANDARD',
        standard_type='其他',category='',status='解析中',source_file=str(path),created_at=now(),is_demo=0,
        warning='',lifecycle='现行',supersedes='')
    values.update({k:v for k,v in metadata.items() if k in values})
    with connect() as db:
        db.execute(f'INSERT INTO documents (document_id,{",".join(values)}) VALUES ({",".join("?" for _ in range(len(values)+1))})',
                   [document_id]+list(values.values()))
    reparse(document_id)
    return document_id
