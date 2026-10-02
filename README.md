# 电力设计规范智能查询 Agent · 本地 V1

面向电力设计工程师的本地资料库、条文检索与来源核对工具。可直接运行，无需配置模型 API。**初始资料全部是虚构 DEMO，不能用于实际工程。**

已部署网页版：<https://gb.sen666.com>（需要登录）。服务器运行与维护见 [服务器部署记录](docs/服务器部署.md)。本地运行仍默认只允许本机；公网部署通过 `ALLOWED_HOSTS` 显式允许域名，并须在反向代理配置登录保护。

## 启动

当前已安装 Python 虚拟环境与依赖。

```powershell
cd 'E:\Syncthing\Oracle-Sync\电力设计规范智能查询 Agent'
.\start.ps1
```

也可双击 `start.bat`。打开 <http://127.0.0.1:8000>。终端 Ctrl+C 停止。端口已占用时不要重复启动。

手动安装与启动：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m backend.seed
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

仅监听本机，V1 无账号和复杂权限。`HOST`/`PORT` 预留配置未用于启动脚本，改端口请调整 uvicorn 参数。

## 使用

1. 规范库 → 上传资料，选择 PDF、DOCX 或 TXT（≤50MB）。填写名称、编号、版本、专业、资料类型、标准分类和版本状态。元数据由管理员核验，不自动猜测编号或版本。
2. 上传后解析原文，保存每条的章节、条号、页码、解析质量和向量。列表可查看解析结果、重解析、修改分类/版本、删除资料。
3. 首页提问，点击引用卡片核对原文与相邻上下文。PDF 原始链接带 `#page=N`，定位效果取决于浏览器 PDF 阅读器。
4. 历史经验、个人判据、厂家资料、典型设计仅显示为参考资料。设计判据页支持新增、编辑、删除，不作为国家/行业依据参与回答。
5. 检索仅采用“已就绪 + 现行”版本；废止、被替代、待核验文档保留在库中供管理员查看。替代关系字段由管理员维护。

## 回答与防编造策略

回答含结论、规范依据、分析、注意事项、可信度和引用卡片。引用内容来自数据库原文，无模型生成条号或条文的通道。

- 没有真实规范候选时，结论包含 **“当前知识库未检索到明确规范依据。”**
- DEMO 自动识别并永久标记，无法仅通过修改表单伪装真实规范。DEMO 命中不计为真实工程依据。
- 真实资料命中时仅报告相关原文，可信度为“中”，需工程师核对适用性；不自动宣称“高”或生成缺乏依据的工程结论。
- 混合检索的相关性门槛不能保证理解所有工程限定条件。相关条文可能不直接支持问题，V1 不自动推断具体设计数值或判定标准冲突。
- 多规范逐条独立展示，禁止自动合并成一个要求。V1 不自动推导差异，缺失的指定编号不会用其他规范冒充。
- 原始资料本身的真实性、现行状态和适用范围仍需人工核验；数据库不会将自编资料变成真实标准。

## 技术与目录

Python 3.14（当前验证环境）、FastAPI、SQLite、pypdf、python-docx、原生 HTML/CSS/JavaScript。前端无需 Node 构建。

```text
frontend/       中文聊天、资料管理、判据、设置
backend/        HTTP API、导入、重解析、Demo 初始化
agent/          领域识别、拆分问题、二次检索、可选证据审核
rag/            BM25、向量、RRF 融合重排
parser/         PDF/DOCX/TXT 条文与章节解析
database/       SQLite schema 与事务
config/         .env 配置
knowledge/      DEMO 与本地 storage
tests/          隔离数据库的自动验收
```

向量持久化到 SQLite，V1 以余弦全量扫描检索，不另启向量数据库服务。关键词采用中文二元词、英文词 BM25；向量默认概念归一化 + 512 维哈希，RRF 融合后考虑条文完整性及指定编号。专业可由检索 API 过滤，Agent 领域识别只提供提示，不硬过滤跨专业问题。版本采用现行状态过滤，不把版本字符串大小当权威优先级。

## 配置 API

编辑根目录 `.env`，重启服务。不要提交 API Key 到版本库。

```dotenv
ALLOW_EXTERNAL_API=true
LLM_BASE_URL=https://your-provider/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=https://your-provider/v1
EMBEDDING_API_KEY=your-embedding-key
EMBEDDING_MODEL=your-embedding-model
TOP_K=10
```

LLM 使用 OpenAI Compatible `/chat/completions`（需该端点兼容），可独立开启；仅选择已有证据 ID，返回不存在的 ID 会拒绝采用并回退。Embedding 使用 `/embeddings`，也可独立配置。不要求两者同一家供应商。

默认 `ALLOW_EXTERNAL_API=false`。**开启后，Embedding 导入时发送条文、检索时发送查询；LLM 发送查询与候选原文。**用户确认可发送的资料后再自行开启。更换 Embedding 模型后重新解析所有文件；不兼容旧向量不会混用。开启远程模型的真实连通性没有验证，因为本次没有提供凭据且未授权传送资料。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node --check frontend/app.js
```

测试使用临时独立数据库，不动实际库。覆盖 PDF 上传与物理页、跨页完整条文、TXT 逻辑页、DOCX 表格、存在条文检索、缺失问题拒绝编造、指定标准缺失、多标准、经验隔离、DEMO 标识、版本过滤、重新解析、删除、空文件/扫描件报错、判据与历史记录、外部调用关闭、跨站请求防护。

手工验证：

- “控制电缆屏蔽层有什么要求？”：出现 DEMO-001/002、3.2.1、原文与页码，显示 DEMO 不能用于工程。
- “DEMO-001 和 DEMO-002 对控制电缆屏蔽层分别怎么规定？”：分别列出处。
- “月球核聚变反应堆安全距离是多少？”：明确无依据，引用为空。
- “紫色端子标记备用芯”：历史经验只能在参考资料中。

## 数据、备份与限制

数据位置 `knowledge/storage/knowledge.sqlite3`，原始文件 `knowledge/storage/files/`。聊天及引用也在本地 SQLite。停服后复制整个 storage 备份（避免漏掉 WAL 文件）。删除文档会删除原始文件和当前索引，聊天中的旧引用快照仍保留，但来源链接失效；重新解析后旧条文 ID 同样失效。

V1 没有 OCR、复杂 PDF 表格结构恢复、自动识别印刷页码、真实语义模型下载、ANN 大规模索引、流式回答、会话语境消歧、自动规范有效性校验或自动冲突判定。DOCX/TXT 明确标逻辑页。超大知识库导入和检索可能慢，导入目前为同步等待。PDF 中异常排版可能退化为章节/页片段，应检查解析结果。

下一阶段建议先选取有合法使用权限的真实规范进行人工条文验收，建立工程问题金标集；再接入经过授权的本地语义 Embedding、OCR、条文修订界面及完整的版本替代关系。检索可靠性验证后，再增加严格逐结论证据核验的工程分析。
