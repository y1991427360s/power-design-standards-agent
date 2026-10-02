"""root 下执行：传入 PBKDF2 哈希（不能传入明文），备份后旋转登录配置。"""
from pathlib import Path
from datetime import datetime
import secrets
import shutil
import sys
import subprocess

root=Path('/opt/power-design-standards-agent')
hash_value=sys.argv[1]
if not hash_value.startswith('pbkdf2_sha256$') or len(hash_value.split('$'))!=3:
    raise ValueError('必须传入 PBKDF2 哈希')
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
env=root/'.env'
shutil.copy2(env,env.with_name('.env.bak-'+stamp))
text='\n'.join(line for line in env.read_text().splitlines() if not line.startswith(('LOGIN_PASSWORD_HASH=','SESSION_SECRET=')))
env.write_text(text+f'\nLOGIN_PASSWORD_HASH={hash_value}\nSESSION_SECRET={secrets.token_hex(32)}\n')
site=Path('/etc/nginx/sites-available/gb.sen666.com')
backup=site.with_name(site.name+'.bak-'+stamp)
shutil.copy2(site,backup)
shutil.copyfile(root/'deploy/gb.sen666.com.nginx',site)
try:
    subprocess.run(['nginx','-t'],check=True)
except Exception:
    shutil.copyfile(backup,site)
    shutil.copyfile(env.with_name('.env.bak-'+stamp),env)
    raise
subprocess.run(['systemctl','restart','power-standards'],check=True)
subprocess.run(['systemctl','reload','nginx'],check=True)
print('已切换单密码登录；旧会话已失效。')
