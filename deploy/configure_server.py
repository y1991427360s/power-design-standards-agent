"""首次部署：以 root 运行；修改已有站点前需人工检查并备份。"""
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import pwd
from datetime import datetime

ROOT = Path('/opt/power-design-standards-agent')
DOMAIN = 'gb.sen666.com'
def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

try:
    account = pwd.getpwnam('powerstandards')
except KeyError:
    run('useradd','--system','--home','/var/lib/power-standards','--shell','/usr/sbin/nologin','powerstandards')
    account = pwd.getpwnam('powerstandards')
data = Path('/var/lib/power-standards')
data.mkdir(exist_ok=True)
data.chmod(0o700)
os.chown(data, account.pw_uid, account.pw_gid)
env = ROOT / '.env'
if env.exists():
    raise RuntimeError('已有 .env，拒绝覆盖。请核对部署状态后再继续。')
env.write_text('DATA_DIR=/var/lib/power-standards\nALLOW_EXTERNAL_API=false\nEMBEDDING_PROVIDER=local\nTOP_K=10\nALLOWED_HOSTS=127.0.0.1,localhost,gb.sen666.com\n',encoding='utf-8')
env.chmod(0o640)
os.chown(env,0,account.pw_gid)
authfile = Path('/etc/nginx/gb.htpasswd')
if not authfile.exists():
    password = secrets.token_urlsafe(24)
    hashed = subprocess.check_output(['openssl','passwd','-apr1','-stdin'],input=(password+'\n').encode()).decode().strip()
    authfile.write_text('ys199:'+hashed+'\n')
    authfile.chmod(0o640)
    os.chown(authfile,0,pwd.getpwnam('www-data').pw_gid)
    credentials = Path('/home/ubuntu/.gb-login.txt')
    credentials.write_text(f'网址：https://{DOMAIN}\n用户名：ys199\n密码：{password}\n方式：浏览器 HTTP Basic 登录。请妥善保管，不要提交到 GitHub。\n',encoding='utf-8')
    credentials.chmod(0o600)
    ubuntu = pwd.getpwnam('ubuntu')
    os.chown(credentials,ubuntu.pw_uid,ubuntu.pw_gid)
site = Path('/etc/nginx/sites-available') / DOMAIN
if site.exists():
    raise RuntimeError('已有站点，拒绝覆盖。')
shutil.copyfile(ROOT/'deploy'/f'{DOMAIN}.nginx', site)
(Path('/etc/nginx/sites-enabled')/DOMAIN).symlink_to(site)
stream = Path('/etc/nginx/stream.d/443-sni.conf')
text = stream.read_text()
needle = 'map $ssl_preread_server_name $tls_backend_443 {'
if needle not in text:
    raise RuntimeError('TLS 分流结构不符合预期，请检查。')
backup = stream.with_name(stream.name+'.bak-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
shutil.copyfile(stream,backup)
if DOMAIN not in text:
    stream.write_text(text.replace(needle,needle+'\n\tgb.sen666.com\t127.0.0.1:9530;',1))
try:
    run('nginx','-t')
except Exception:
    shutil.copyfile(backup,stream)
    (Path('/etc/nginx/sites-enabled')/DOMAIN).unlink()
    raise
shutil.copyfile(ROOT/'deploy/power-standards.service','/etc/systemd/system/power-standards.service')
run('sudo','-u','powerstandards',str(ROOT/'.venv/bin/python'),'-m','backend.seed',cwd=ROOT)
run('systemctl','daemon-reload')
run('systemctl','enable','--now','power-standards.service')
run('systemctl','reload','nginx')
print('独立服务与 TLS 站点已配置。')
