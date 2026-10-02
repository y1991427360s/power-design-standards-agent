import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')
DATA = Path(os.getenv('DATA_DIR', str(ROOT / 'knowledge' / 'storage')))
DATA.mkdir(parents=True, exist_ok=True)
FILES = DATA / 'files'
FILES.mkdir(exist_ok=True)
DB = DATA / 'knowledge.sqlite3'
TOP_K = max(1, min(30, int(os.getenv('TOP_K', '10'))))
ALLOW_EXTERNAL = os.getenv('ALLOW_EXTERNAL_API', 'false').lower() == 'true'
SOURCE_TYPES = ['STANDARD', 'ENTERPRISE_STANDARD', 'TYPICAL_DESIGN', 'PROJECT_EXPERIENCE', 'PERSONAL_RULE', 'MANUFACTURER']
STANDARD_TYPES = ['国家标准', '行业标准', '能源行业标准', '国网企业标准', '南网企业标准', '设计院内部规定', '其他']
