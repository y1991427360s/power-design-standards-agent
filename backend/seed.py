import shutil
from config.settings import ROOT, FILES
from database.store import init_db, connect
from backend.services import import_document

def main():
    init_db()
    for filename, code, source in [('demo_standard.txt','DEMO-001','STANDARD'),('demo_comparison.txt','DEMO-002','ENTERPRISE_STANDARD'),('demo_experience.txt','DEMO-EXP','PROJECT_EXPERIENCE')]:
        with connect() as db:
            if db.execute('SELECT 1 FROM documents WHERE standard_code=?',(code,)).fetchone(): continue
        path = FILES / filename
        shutil.copyfile(ROOT/'knowledge'/filename,path)
        import_document(path,{'standard_name':'测试用电力设计资料 '+code,'standard_code':code,'version':'2026 测试版',
            'source_type':source,'category':'电缆','standard_type':'其他','is_demo':1})
    print('DEMO 已初始化（非真实规范）。')

if __name__ == '__main__': main()
