import hashlib
import json
from evaluation.metrics import ranking_metrics, document_ranking, matches


def evaluate(questions, mode='demo'):
    from database.store import all_clauses
    from rag.search import search
    from agent.query import answer, NO_EVIDENCE
    from rag.embeddings import Embeddings
    from config.settings import ALLOW_EXTERNAL
    if ALLOW_EXTERNAL:
        raise ValueError('Evaluation requires external APIs disabled; use the isolated CLI')
    corpus = all_clauses()
    if mode not in ('demo', 'real'):
        raise ValueError('Unknown evaluation mode')
    if mode == 'real' and any(r['is_demo'] for r in corpus):
        raise ValueError('Real evaluation requires a corpus without eligible DEMO documents; use a separate evaluation library')
    if Embeddings().provider != 'local':
        raise ValueError('This offline baseline requires local embeddings')
    # Missing labels are a dataset error, not silently counted as retrieval failures.
    for q in questions:
        for group in [[d] for d in q.expected_documents] + q.groups():
            if not any(any(matches(r, t, bool(t.clause)) and r['source_type'] in ('STANDARD','ENTERPRISE_STANDARD') and (mode == 'demo' or not r['is_demo'])
                           for t in group) for r in corpus):
                raise ValueError(f'{q.id}: expected evidence absent from eligible corpus')
    details = []
    fields = ('standard_code','standard_name','version','clause','page','page_end','page_kind',
              'source_type','is_demo','keyword_score','vector_score','rrf_score','completeness_bonus',
              'standard_number_bonus','category_bonus','final_score','keyword_rank','vector_rank')
    for q in questions:
        rows = search(q.question, source_types=['STANDARD','ENTERPRISE_STANDARD'], top_k=10, debug=True)
        if mode == 'real':
            rows = [r for r in rows if not r['is_demo']]
        detail = {'question':q.model_dump(), 'retrieved':[{k:r[k] for k in fields} for r in rows]}
        if q.negative:
            result = answer(q.question)
            formal = [r for r in result['citations'] if not r['is_demo'] and r['source_type'] in ('STANDARD','ENTERPRISE_STANDARD')]
            detail.update(rejected=result['conclusion'].startswith(NO_EVIDENCE) and not formal,
                          false_formal_evidence=bool(formal))
        else:
            detail['document'] = ranking_metrics(document_ranking(rows), [[t] for t in q.expected_documents])
            detail['clause'] = ranking_metrics(rows, q.groups(), clause=True)
            detail['failed'] = detail['clause']['recall@10'] < 1 or detail['document']['recall@10'] < 1
        details.append(detail)
    positives = [d for d in details if 'clause' in d]
    negatives = [d for d in details if 'rejected' in d]
    summary = {kind:{key:sum(d[kind][key] for d in positives)/len(positives)
                     for key in positives[0][kind]} if positives else None for kind in ('document','clause')}
    summary.update(total_questions=len(details), positive_questions=len(positives), negative_questions=len(negatives),
                   negative_rejection_accuracy=sum(d['rejected'] for d in negatives)/len(negatives) if negatives else None,
                   negative_false_formal_rate=sum(d['false_formal_evidence'] for d in negatives)/len(negatives) if negatives else None)
    fingerprint = sorted((r['standard_code'],r['version'],r['clause'],r['text'],r['source_type'],r['is_demo'],r['embedding_id'],r['vector']) for r in corpus)
    return {'schema_version':1,'mode':mode,'scope':'DEMO flow validation only' if mode=='demo' else 'Human-labelled corpus snapshot',
            'corpus_sha256':hashlib.sha256(json.dumps(fingerprint,ensure_ascii=False).encode()).hexdigest(),
            'algorithm':{'rrf_constant':60,'minimum_overlap':0.12,'requires_positive_bm25':True,
                         'completeness_multiplier':1.08,'standard_number_multiplier':1.3,
                         'category_filter':'not applied','llm_selection':'disabled'},
            'retrieval_depth':10,'embedding':Embeddings().identity,'eligible_clauses':len(corpus),
            'summary':summary,'details':details}
