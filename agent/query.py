import re
from rag.search import search
from agent.provider import LLMProvider
from config.settings import TOP_K

NO_EVIDENCE = '当前知识库未检索到明确规范依据。'
DOMAINS = {'电缆':['电缆','屏蔽'], '继电保护':['继电保护','保护装置'], '电气二次':['端子','二次','ct','pt','互感器'],
           '通信':['通信','光缆'], '电气一次':['主变','开关','母线']}

def search_standard(question, **kwargs):
    return search(question, source_types=['STANDARD','ENTERPRISE_STANDARD'], **kwargs)

def answer(question, document_ids=None, top_k=TOP_K):
    domain = next((name for name, words in DOMAINS.items() if any(w in question.lower() for w in words)), '未限定')
    queries = [question] + [part.strip() for part in re.split('[？?；;\n]',question) if len(part.strip()) >= 4 and part.strip() != question]
    trace = [{'tool':'领域识别','detail':domain}]
    found = {}
    for query in queries[:4]:
        hits = search_standard(query,document_ids=document_ids,top_k=top_k)
        trace.append({'tool':'search_standard','detail':query, 'count':len(hits)})
        for row in hits: found[row['id']] = row
    rows = sorted(found.values(),key=lambda r:r['score'],reverse=True)[:top_k]
    if not rows:
        # 单次扩展检索；相同证据阈值，不因扩大召回降低依据标准。
        expanded = question.replace('如何','').replace('怎么','').replace('请问','')
        if expanded != question:
            rows = search_standard(expanded,document_ids=document_ids,top_k=top_k)
            trace.append({'tool':'search_standard（二次检索）','detail':expanded,'count':len(rows)})
    warnings = []
    try:
        selected = LLMProvider().select(question,rows) if rows else None
        if selected is not None:
            rows = [r for r in rows if r['id'] in selected]
            trace.append({'tool':'模型证据审核','detail':'仅接受知识库中已有证据 ID'})
    except Exception:
        warnings.append('模型证据审核不可用，已回退到本地原文检索。')
    formal = [r for r in rows if not r['is_demo']]
    reference = search(question,source_types=['TYPICAL_DESIGN','PROJECT_EXPERIENCE','PERSONAL_RULE','MANUFACTURER'],document_ids=document_ids,top_k=3)
    if not formal:
        conclusion = NO_EVIDENCE
        if rows: conclusion += ' 以下仅为 DEMO 测试条文，不能用于实际工程设计。'
    else:
        conclusion = '检索到以下相关原文，尚需核对适用条件后才能形成工程结论：'
    analysis = '采用原文摘录模式，按资料分别展示，不自动合并不同规范，也不推断未被原文支持的工程要求。'
    if not rows: analysis += ' 当前知识库未检索到能够直接支持该结论的明确规范条文。'
    if len({r['document_id'] for r in rows}) > 1:
        analysis += ' 多份资料命中：请逐一对照下方条文；系统不自动判定标准间的优先级或冲突。'
    notes = ['检索相似度不等于条文适用性，请核对电压等级、范围、例外、版本和实施日期。',
             '页码为原始 PDF 物理页；TXT/DOCX 显示逻辑页，不冒充印刷页码。'] + warnings
    if any(r['is_demo'] for r in rows): notes.append('DEMO / 非真实规范：仅用于验证系统流程。')
    return {'conclusion':conclusion,'analysis':analysis,'notes':notes,'confidence':'中' if formal else '低',
            'confidence_reason':'存在相关原文，尚未自动确认直接适用性。' if formal else '缺少真实、明确规范依据。',
            'citations':rows,'references':reference,'trace':trace,'domain':domain}
