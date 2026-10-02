import json
import math
import re
from collections import Counter
from database.store import all_clauses
from rag.embeddings import Embeddings, tokens, cosine
from config.settings import TOP_K

def search(query, source_types=None, category='', document_ids=None, top_k=TOP_K, debug=False):
    rows = [r for r in all_clauses() if (not source_types or r['source_type'] in source_types)
            and (not category or r['category'] == category)
            and (not document_ids or r['document_id'] in document_ids)]
    if not rows: return []
    embedding = Embeddings()
    rows = [r for r in rows if r['embedding_id'] == embedding.identity]
    if not rows: raise ValueError('向量模型已变更，请重新解析文档建立索引。')
    qvec = embedding.embed([query])[0]
    qt = set(tokens(query))
    counts = [Counter(tokens(r['text'])) for r in rows]
    avg = sum(sum(c.values()) for c in counts) / max(1,len(rows)) or 1
    df = {t: sum(t in c for c in counts) for t in qt}
    scored = []
    requested_codes = re.findall(r'(?:GB(?:/T)?|DL(?:/T)?|NB(?:/T)?|DEMO)[\s-]*\d+(?:-\d+)?', query, re.I)
    for row, count in zip(rows, counts):
        if row['text'].strip() == (row['title'] or '').strip():
            continue  # 仅有章节标题，没有可支持工程要求的正文。
        if requested_codes and not any(re.sub(r'\s','',c).lower() == re.sub(r'\s','',row['standard_code']).lower() for c in requested_codes):
            continue
        length = sum(count.values())
        bm25 = sum(math.log(1+(len(rows)-df[t]+0.5)/(df[t]+0.5)) * count[t]*2.2 /
                    (count[t]+1.2*(0.25+0.75*length/avg)) for t in qt if count[t])
        overlap = len(qt & set(count)) / max(1,len(qt))
        vector = cosine(qvec, json.loads(row['vector']))
        # 硬证据门槛：纯向量偶然相似不得成为规范依据。
        if overlap < 0.12 or bm25 <= 0: continue
        scored.append({**row, 'bm25_score': round(bm25,4), 'vector_score': round(vector,4),
                       'overlap': round(overlap,4), 'score': 0.0})
    lexical = sorted(scored,key=lambda r:r['bm25_score'],reverse=True)
    semantic = sorted(scored,key=lambda r:r['vector_score'],reverse=True)
    ranks = {r['id']: i+1 for i,r in enumerate(semantic)}
    for i,row in enumerate(lexical):
        score = 1/(60+i+1)+1/(60+ranks[row['id']])
        rrf = score
        if row['clause']: score *= 1.08
        if category and row['category'] == category: score *= 1.05
        if requested_codes and any(re.sub(r'\s','',c).lower() in re.sub(r'\s','',row['standard_code']).lower() for c in requested_codes): score *= 1.3
        row['score'] = round(score,6)
        if debug:
            row.update(keyword_score=row['bm25_score'], rrf_score=rrf,
                       completeness_bonus=1.08 if row['clause'] else 1.0,
                       standard_number_bonus=1.3 if requested_codes else 1.0,
                       category_bonus=1.05 if category and row['category'] == category else 1.0,
                       final_score=row['score'], keyword_rank=i+1, vector_rank=ranks[row['id']])
    return sorted(lexical,key=lambda r:r['score'],reverse=True)[:max(1,min(30,top_k))]
