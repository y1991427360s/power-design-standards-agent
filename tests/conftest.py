import os
import tempfile
from pathlib import Path
os.environ['DATA_DIR'] = tempfile.mkdtemp(prefix='power-agent-tests-')
os.environ['ALLOW_EXTERNAL_API'] = 'false'
os.environ['EMBEDDING_PROVIDER'] = 'local'
os.environ['LLM_MODEL'] = ''
os.environ['ALLOWED_HOSTS'] = '127.0.0.1,localhost,testserver'
os.environ.pop('LOGIN_PASSWORD_HASH',None)
os.environ.pop('SESSION_SECRET',None)
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from database.store import connect

@pytest.fixture
def client():
    with TestClient(app) as client:
        with connect() as db:
            for table in ('messages','conversations','rules','clauses','documents'): db.execute('DELETE FROM '+table)
        yield client
