import json
from pathlib import Path


def markdown(result):
    lines = ['# RAG evaluation', '', result['scope'], '',
             'Document metrics use deduplicated document ranks. Clause metrics use evidence ranks.',
             'Hit means any correct target; Recall measures required groups covered; MRR is truncated at 10.',
             'Keyword labels are diagnostic only, never substitutes for evidence.', '']
    for key, value in result['summary'].items():
        if isinstance(value, dict):
            lines.extend(f'{key} {metric}: {score:.4f}' for metric, score in value.items())
        else:
            lines.append(f'{key}: {value}')
    for d in result['details']:
        q = d['question']
        lines += ['', f'## {q["id"]}: {q["question"]}', '',
                  'Expected: ' + json.dumps({'documents':q['expected_documents'],'clauses':q['expected_clauses'],
                                           'groups':q['clause_groups']},ensure_ascii=False), '',
                  'Outcome: ' + json.dumps({k:v for k,v in d.items() if k not in ('question','retrieved')},ensure_ascii=False), '',
                  '|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|',
                  '|---|---|---|---|---|---|---|---|---|']
        for i,r in enumerate(d['retrieved'],1):
            label = (r['standard_code']+' / '+r['version']).replace('|','\\|').replace('\n',' ')
            lines.append(f'|{i}|{label}|{r["clause"]}|{r["keyword_score"]}|{r["vector_score"]}|{r["rrf_score"]:.6f}|{r["completeness_bonus"]}|{r["standard_number_bonus"]}|{r["final_score"]}|')
        if not d['retrieved']:
            lines.append('No retrieved evidence.')
    return '\n'.join(lines)+'\n'


def write_report(result, directory):
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    (path/'rag-evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    text = markdown(result)
    (path/'rag-evaluation.md').write_text(text,encoding='utf-8')
    return text
