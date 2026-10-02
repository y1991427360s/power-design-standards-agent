"""单密码登录；服务器仅存 PBKDF2 哈希与会话签名密钥。"""
import hashlib
import hmac
import os
import secrets
import time
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

COOKIE = 'standards_session'
TTL = 43200

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),260000).hex()
    return f'pbkdf2_sha256${salt}${digest}'

def enabled(): return bool(os.getenv('LOGIN_PASSWORD_HASH'))

def verify_password(password):
    saved = os.getenv('LOGIN_PASSWORD_HASH','')
    try:
        algorithm, salt, digest = saved.split('$')
        return algorithm == 'pbkdf2_sha256' and hmac.compare_digest(password_hash(password,salt),saved)
    except ValueError:
        return False

def signature(payload):
    secret = os.getenv('SESSION_SECRET','')
    if not secret: raise ValueError('启用登录时必须配置 SESSION_SECRET')
    return hmac.new(secret.encode(),payload.encode(),hashlib.sha256).hexdigest()

def valid_session(request):
    try:
        payload, sig = request.cookies.get(COOKIE,'').rsplit('.',1)
        issued = int(payload.split(':',1)[0])
        return 0 <= time.time()-issued < TTL and hmac.compare_digest(signature(payload),sig)
    except (ValueError,TypeError): return False

def login_response(password, secure):
    if not enabled(): return JSONResponse({'detail':'未启用密码登录'},status_code=400)
    if not verify_password(password): return JSONResponse({'detail':'密码不正确'},status_code=401)
    payload = f'{int(time.time())}:{secrets.token_hex(16)}'
    response = JSONResponse({'ok':True})
    response.set_cookie(COOKIE,payload+'.'+signature(payload),max_age=TTL,httponly=True,secure=secure,samesite='strict',path='/')
    response.headers['Cache-Control']='no-store'
    return response

def login_page():
    return HTMLResponse('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>登录 · 电力设计规范查询</title>
<style>body{margin:0;background:#f3f5f8;color:#25364b;font:15px "Microsoft YaHei",sans-serif;display:grid;place-items:center;min-height:100vh}main{background:white;padding:36px;border:1px solid #dde4ec;border-radius:10px;width:min(340px,80vw)}h1{font-size:22px}p{color:#718297;line-height:1.7}input,button{box-sizing:border-box;width:100%;padding:13px;border-radius:6px;font:inherit;margin-top:12px}input{border:1px solid #ccd6e0}button{border:0;background:#235b8c;color:white;cursor:pointer}#error{color:#a3432f;font-size:13px}</style>
<main><h1>电力设计规范查询</h1><p>输入访问密码，进入规范知识库。</p><form id="login"><label for="password">访问密码</label><input id="password" type="password" required autocomplete="current-password" autofocus maxlength="256"><button id="submit">登录</button><p id="error" role="alert"></p></form></main>
<script>document.querySelector('#login').onsubmit=async e=>{e.preventDefault();const b=document.querySelector('#submit');b.disabled=true;document.querySelector('#error').textContent='';try{const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:document.querySelector('#password').value})});if(!r.ok){const d=await r.json();throw Error(d.detail||'登录失败');}location.replace('/');}catch(err){document.querySelector('#error').textContent=err.message;}finally{b.disabled=false;}};</script></html>''',headers={'Cache-Control':'no-store'})
