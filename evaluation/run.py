"""Run in a fresh subprocess: never patch a live application's database globals."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default=str(ROOT/'tests/golden/questions.json'))
    parser.add_argument('--database', help='Existing SQLite file; read-only online snapshot, never modified')
    parser.add_argument('--mode', choices=('demo','real'), default='demo')
    parser.add_argument('--output', default=str(ROOT/'reports'))
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.worker:
        if args.mode == 'real' and not args.database:
            parser.error('--mode real requires --database')
        with tempfile.TemporaryDirectory(prefix='rag-evaluation-') as directory:
            if args.database:
                source = Path(args.database).resolve()
                with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src:
                    with closing(sqlite3.connect(str(Path(directory)/'knowledge.sqlite3'))) as dest:
                        src.backup(dest)
            env = dict(os.environ, DATA_DIR=directory, ALLOW_EXTERNAL_API='false', EMBEDDING_PROVIDER='local',
                       LLM_MODEL='', LOGIN_PASSWORD_HASH='', SESSION_SECRET='',
                       ALLOWED_HOSTS='127.0.0.1,localhost,testserver', RAG_EVALUATION_WORKER='1')
            command = [sys.executable,'-m','evaluation.run','--worker','--dataset',str(Path(args.dataset).resolve()),
                       '--mode',args.mode,'--output',str(Path(args.output).resolve())]
            if args.database:
                command += ['--database','snapshot']
            return subprocess.run(command,env=env,cwd=ROOT).returncode
    if os.getenv('RAG_EVALUATION_WORKER') != '1' or not Path(os.getenv('DATA_DIR','')).name.startswith('rag-evaluation-'):
        parser.error('Worker must be launched by the isolated evaluation parent')
    from evaluation.models import load_dataset
    from evaluation.evaluator import evaluate
    from evaluation.report import write_report
    if not args.database:
        from backend.seed import main as seed
        seed()
    result = evaluate(load_dataset(args.dataset),args.mode)
    result['dataset_sha256'] = hashlib.sha256(Path(args.dataset).read_bytes()).hexdigest()
    result['code_revision'] = subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
    result['working_tree_dirty'] = bool(subprocess.run(['git','status','--porcelain'],cwd=ROOT,capture_output=True,text=True).stdout)
    write_report(result,args.output)
    print(result['scope'])
    summary = result['summary']
    print(f'Total Questions: {summary["total_questions"]} (positive: {summary["positive_questions"]}, negative: {summary["negative_questions"]})')
    for kind in ('document','clause'):
        if summary[kind]:
            for metric,value in summary[kind].items():
                print(f'{kind.title()} {metric}: {value:.4f}' if metric == 'mrr' else f'{kind.title()} {metric}: {value:.1%}')
    for key in ('negative_rejection_accuracy','negative_false_formal_rate'):
        value = summary[key]
        print(f'{key}: {value:.1%}' if value is not None else f'{key}: N/A')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
