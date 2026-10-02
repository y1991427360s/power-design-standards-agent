from backend.auth import password_hash, COOKIE

def test_password_only_session_and_logout(client, monkeypatch):
    monkeypatch.setenv('LOGIN_PASSWORD_HASH',password_hash('test-only-password'))
    monkeypatch.setenv('SESSION_SECRET','test-session-secret')
    assert client.get('/',follow_redirects=False).status_code==303
    assert client.get('/api/documents').status_code==401
    page=client.get('/login').text
    assert '访问密码' in page and 'username' not in page
    assert client.post('/api/login',json={'password':'incorrect'}).status_code==401
    response=client.post('/api/login',json={'password':'test-only-password'})
    assert response.status_code==200 and 'HttpOnly' in response.headers['set-cookie']
    assert client.get('/api/documents').status_code==200
    assert client.post('/api/logout').status_code==200
    assert client.get('/api/documents').status_code==401
    client.cookies.set(COOKIE,'0:fake.invalid')
    assert client.get('/api/documents').status_code==401

def test_session_rotation_rejects_old_cookie(client,monkeypatch):
    monkeypatch.setenv('LOGIN_PASSWORD_HASH',password_hash('test-only-password'))
    monkeypatch.setenv('SESSION_SECRET','before')
    client.post('/api/login',json={'password':'test-only-password'})
    monkeypatch.setenv('SESSION_SECRET','after')
    assert client.get('/api/documents').status_code==401
