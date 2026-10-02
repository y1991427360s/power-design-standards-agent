import hashlib
import math
import os
import re
import httpx
from config.settings import ALLOW_EXTERNAL

CONCEPTS = {'电流互感器': 'ct', '电压互感器': 'pt', '接地线': '接地', '接地导体': '接地',
            '缆线': '电缆', '光缆': '通信电缆', '保护装置': '继电保护'}

def normalize(text):
    text = text.lower()
    for original, replacement in CONCEPTS.items():
        text = text.replace(original, replacement)
    return text

def tokens(text):
    text = normalize(text)
    words = re.findall(r'[a-z0-9]+(?:[./-][a-z0-9]+)*', text)
    for run in re.findall(r'[\u4e00-\u9fff]+', text):
        words += [run[i:i+2] for i in range(len(run)-1)]
        if len(run) == 1: words.append(run)
    return words

class Embeddings:
    def __init__(self):
        self.provider = os.getenv('EMBEDDING_PROVIDER', 'local')
        self.model = os.getenv('EMBEDDING_MODEL', '')
        if self.provider not in ('local', 'openai'):
            raise ValueError('EMBEDDING_PROVIDER 只支持 local/openai')
        self.identity = 'local-concept-hash-v1' if self.provider == 'local' else f'openai:{os.getenv("EMBEDDING_BASE_URL", "")}:{self.model}'

    def embed(self, texts):
        if self.provider == 'openai':
            if not ALLOW_EXTERNAL:
                raise ValueError('外部 API 未授权：请先确认数据发送范围，再设置 ALLOW_EXTERNAL_API=true。')
            if not self.model: raise ValueError('请配置 EMBEDDING_MODEL')
            url = os.getenv('EMBEDDING_BASE_URL', '').rstrip('/') + '/embeddings'
            with httpx.Client(timeout=60) as client:
                response = client.post(url, headers={'Authorization': 'Bearer ' + os.getenv('EMBEDDING_API_KEY', '')},
                    json={'model': self.model, 'input': texts})
                response.raise_for_status()
                data = sorted(response.json()['data'], key=lambda x: x['index'])
                vectors = [row['embedding'] for row in data]
                if len(vectors) != len(texts): raise ValueError('Embedding API 返回数量不符')
                return vectors
        vectors = []
        for text in texts:
            vector = [0.0] * 512
            for token in tokens(text):
                n = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], 'big')
                vector[n % 512] += 1.0 if n & 512 else -1.0
            length = math.sqrt(sum(v*v for v in vector)) or 1
            vectors.append([v/length for v in vector])
        return vectors

def cosine(a, b):
    if len(a) != len(b): return 0.0
    norm = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
    return sum(x*y for x,y in zip(a,b)) / norm if norm else 0.0
