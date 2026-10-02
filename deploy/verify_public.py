"""验证 HTTPS 登录保护与核心查询。凭据文件必须位于仓库之外。"""
import json
import sys
from pathlib import Path
import httpx

def main():
    values = {}
    for line in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
        if '：' in line:
            key, value = line.split('：',1)
            values[key] = value.strip()
    url = values['网址']
    with httpx.Client(base_url=url, timeout=30) as client:
        assert client.get('/').status_code == 401
        assert client.get('/api/documents').status_code == 401
        client.auth = (values['用户名'],values['密码'])
        response = client.get('/')
        assert response.status_code == 200 and '电力设计规范' in response.text
        docs = client.get('/api/documents').json()
        assert len(docs) >= 3
        good = client.post('/api/chat',json={'question':'DEMO-001 和 DEMO-002 对控制电缆屏蔽层分别怎么规定？'}).json()
        assert {'DEMO-001','DEMO-002'} <= {c['standard_code'] for c in good['citations']}
        assert any(c['clause']=='3.2.1' and c['page']==1 for c in good['citations'])
        assert all(c['is_demo'] for c in good['citations'])
        missing = client.post('/api/chat',json={'question':'月球核聚变反应堆安全距离是多少？'}).json()
        assert missing['conclusion'] == '当前知识库未检索到明确规范依据。'
        assert not missing['citations']
        clause = good['citations'][0]
        assert client.get('/api/clauses/'+clause['id']).status_code==200
        assert client.get('/api/documents/'+clause['document_id']+'/file').status_code==200
        assert client.post('/api/chat',json={'question':'测试'},headers={'Origin':'https://evil.example'}).status_code==403
        print(json.dumps({'https':True,'authentication':'passed','homepage':200,'documents':len(docs),
                          'citations':'passed','missing_evidence':'passed','cross_site':'blocked'},ensure_ascii=False))

if __name__ == '__main__': main()
