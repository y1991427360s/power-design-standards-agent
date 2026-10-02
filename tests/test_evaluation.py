import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import pytest
from evaluation.models import load_dataset, Question, Target
from evaluation.metrics import ranking_metrics, document_ranking
from evaluation.evaluator import evaluate
from evaluation.report import write_report
from tests.test_acceptance import upload, query

ROOT = Path(__file__).resolve().parent.parent


def target(code='A', clause='1.0.1'):
    return Target(standard_code=code,version='2026',clause=clause)


def row(code='A',clause='1.0.1'):
    return dict(standard_code=code,version='2026',clause=clause)


def test_golden_load():
    questions = load_dataset(ROOT/'tests/golden/questions.json')
    assert len(questions)==12 and sum(q.negative for q in questions)==3
    assert any(q.clause_groups for q in questions)


def test_hit_recall_and_mrr():
    metrics = ranking_metrics([row('X'),row(),row('B')],[[target()],[target('B')]],True)
    assert metrics['hit@1']==0 and metrics['hit@3']==1
    assert metrics['recall@1']==0 and metrics['recall@3']==1 and metrics['mrr']==0.5
    assert ranking_metrics([row('X')],[[target()]],True)['mrr']==0


def test_alternative_groups_and_multiple_required():
    groups = [[target('A'),target('B')],[target('C')]]
    result = ranking_metrics([row('B')],groups,True)
    assert result['hit@1']==1 and result['recall@1']==0.5
    assert ranking_metrics([row('B'),row('C')],groups,True)['recall@3']==1


def test_document_clause_separate_and_deduplicated():
    rows = [row('A','9.9.9'),row('A','8.8.8'),row('B')]
    assert len(document_ranking(rows))==2
    assert ranking_metrics(document_ranking(rows),[[target('B')]])['mrr']==0.5
    assert ranking_metrics(rows,[[target('A')]],True)['hit@10']==0
    assert ranking_metrics(document_ranking(rows),[[target('A')]])['hit@1']==1


@pytest.mark.parametrize('change', [dict(negative=True),dict(expected_clauses=[]),dict(clause_groups=[[]])])
def test_invalid_labels(change):
    payload=dict(id='Q',question='测试问题',domain='测试',expected_documents=[target(clause=None).model_dump()],expected_clauses=[target().model_dump()])
    payload.update(change)
    with pytest.raises(ValueError): Question.model_validate(payload)


def test_duplicate_ids_rejected(tmp_path):
    payload=dict(id='Q',question='测试问题',domain='测试',negative=True)
    file=tmp_path/'duplicate.json'; file.write_text(json.dumps([payload,payload]),encoding='utf-8')
    with pytest.raises(ValueError): load_dataset(file)


def test_negative_false_formal_and_no_chat_writes(client):
    upload(client,'3.2.1 控制电缆屏蔽层应连接测试接地端子。')
    q=Question(id='N',question='控制电缆屏蔽层',domain='测试',negative=True)
    result=evaluate([q])
    assert result['summary']['negative_rejection_accuracy']==0
    assert result['summary']['negative_false_formal_rate']==1
    assert client.get('/api/conversations').json()==[]


def test_demo_negative_is_not_formal(client):
    upload(client,'DEMO / 非真实规范\n3.2.1 控制电缆屏蔽层应连接测试端子。')
    q=Question(id='N',question='控制电缆屏蔽层',domain='测试',negative=True)
    assert evaluate([q])['summary']['negative_rejection_accuracy']==1
    with pytest.raises(ValueError): evaluate([q],'real')


def test_debug_and_api_unchanged(client):
    upload(client,'3.2.1 控制电缆屏蔽层应连接测试接地端子。')
    from rag.search import search
    normal=search('控制电缆屏蔽层')
    debug=search('控制电缆屏蔽层',debug=True)
    assert [r['id'] for r in normal]==[r['id'] for r in debug]
    assert [r['score'] for r in normal]==[r['final_score'] for r in debug]
    r=debug[0]
    assert r['final_score']==round(r['rrf_score']*r['completeness_bonus']*r['standard_number_bonus']*r['category_bonus'],6)
    result=query(client,'控制电缆屏蔽层')
    assert result['citations'] and 'rrf_score' not in result['citations'][0]
    assert client.get('/').status_code==200 and client.get('/app.js').status_code==200


def test_missing_gold_is_error(client):
    q=Question(id='Q',question='测试问题',domain='测试',expected_documents=[target(clause=None)],expected_clauses=[target()])
    with pytest.raises(ValueError,match='absent'): evaluate([q])


def test_cli_isolation_and_readonly_snapshot(tmp_path):
    database=tmp_path/'original.sqlite3'
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE marker(value TEXT)')
        db.execute("INSERT INTO marker VALUES ('preserve')")
    before=hashlib.sha256(database.read_bytes()).hexdigest()
    # Default CLI must ignore inherited DATA_DIR and seed only its temp library.
    import os
    env=dict(os.environ,DATA_DIR=str(tmp_path),LOGIN_PASSWORD_HASH='production-placeholder',SESSION_SECRET='production-placeholder')
    output=tmp_path/'report'
    p=subprocess.run([sys.executable,'-m','evaluation.run','--output',str(output)],cwd=ROOT,env=env,capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    assert not (tmp_path/'knowledge.sqlite3').exists()
    report=json.loads((output/'rag-evaluation.json').read_text(encoding='utf-8'))
    assert report['summary']['total_questions']==12
    assert 'source_file' not in (output/'rag-evaluation.json').read_text(encoding='utf-8')
    # Invalid source schema fails in worker, but source bytes stay identical.
    p=subprocess.run([sys.executable,'-m','evaluation.run','--database',str(database),'--output',str(output)],cwd=ROOT,env=env,capture_output=True,text=True)
    assert p.returncode!=0
    assert hashlib.sha256(database.read_bytes()).hexdigest()==before


def test_snapshot_evaluation_preserves_existing_data(client,tmp_path):
    from config.settings import DB
    upload(client,'3.2.1 控制电缆屏蔽层应连接测试接地端子。')
    dataset=tmp_path/'gold.json'
    dataset.write_text(json.dumps([dict(id='Q',question='控制电缆屏蔽层',domain='电缆',
        expected_documents=[dict(standard_code='TEST-001',version='2026')],
        expected_clauses=[dict(standard_code='TEST-001',version='2026',clause='3.2.1')])]),encoding='utf-8')
    from database.store import connect
    with connect() as db:
        before=[tuple(r) for r in db.execute('SELECT * FROM clauses')]
    p=subprocess.run([sys.executable,'-m','evaluation.run','--mode','real','--database',str(DB),
                      '--dataset',str(dataset),'--output',str(tmp_path/'output')],cwd=ROOT,capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    with connect() as db:
        assert [tuple(r) for r in db.execute('SELECT * FROM clauses')]==before
        assert db.execute('SELECT COUNT(*) FROM messages').fetchone()[0]==0
    result=json.loads((tmp_path/'output/rag-evaluation.json').read_text(encoding='utf-8'))
    assert result['summary']['clause']['hit@1']==1


def test_evaluator_blocks_external_api(client,monkeypatch):
    import config.settings
    monkeypatch.setattr(config.settings,'ALLOW_EXTERNAL',True)
    q=Question(id='N',question='测试问题',domain='测试',negative=True)
    with pytest.raises(ValueError,match='external APIs disabled'): evaluate([q])


def test_worker_cannot_bypass_isolation():
    import os
    env=dict(os.environ)
    env.pop('RAG_EVALUATION_WORKER',None)
    p=subprocess.run([sys.executable,'-m','evaluation.run','--worker'],cwd=ROOT,env=env,capture_output=True,text=True)
    assert p.returncode!=0 and 'isolated evaluation parent' in p.stderr


def test_mrr_truncated_and_required_groups():
    m=ranking_metrics([row('X')]*10+[row()],[[target()]],True)
    assert m['mrr']==0 and m['hit@10']==0
    m=ranking_metrics([row()],[[target()],[target('B')]],True)
    assert m['hit@1']==1 and m['recall@10']==0.5


def test_failed_question_diagnostic_report(client,tmp_path):
    upload(client,'3.2.1 控制电缆屏蔽层应连接测试接地端子。')
    q=Question(id='FAIL',question='月球核聚变反应堆安全距离是多少？',domain='测试',
               expected_documents=[Target(standard_code='TEST-001',version='2026')],
               expected_clauses=[Target(standard_code='TEST-001',version='2026',clause='3.2.1')])
    result=evaluate([q])
    assert result['details'][0]['failed'] and result['summary']['clause']['mrr']==0
    text=write_report(result,tmp_path)
    assert 'Expected:' in text and 'TEST-001' in text and 'No retrieved evidence.' in text
