# Golden Dataset

questions.json 是自编 DEMO 评测集，不能证明真实工程检索准确率。真实资料和金标应放在仓库外，运行时用 --dataset 指定。

顶层为问题数组，id 唯一；question 是实际输入，domain 仅用于标注，不改变检索；notes 和 applicable_conditions 记录人工核验。expected_keywords 仅帮助诊断，不参与命中计算。

expected_documents 使用对象 {"standard_code":"DEMO-001","version":"2026 测试版"}。expected_clauses 增加 "clause":"3.2.1"。精确匹配编号、版本和条号；不使用重解析后会变化的数据库 UUID。

expected_clauses 中每个条文都为必需答案。允许多个条文择一时，改用 clause_groups：外层每组都必须覆盖，组内任何条文都可满足；不可同时填写非空 expected_clauses。跨规范问题分别建立必需组。所有条文的规范都必须列入 expected_documents。Document Recall 将列出的所有规范视为必需；跨规范择一主要查看 Clause Recall，Document Recall 仍统计各规范覆盖。

negative=true 时两类期望和 clause_groups 必须为空。含有真实正式依据则为误报；拒答指标同时要求无正式依据且结论以固定无依据提示开头。DEMO 引用不计正式依据，所以必须另外看正题检索指标，不能仅用 DEMO 的拒答率判断安全性。

Hit@K 表示前 K 至少命中一个正确目标；Recall@K 表示覆盖必需目标/组的比例；MRR 为首个正确结果倒数排名，未命中记零，截断深度 10。文档指标先去重，再按文档排名计算，只有前 10 条 evidence 所代表的文档可见；条文指标按原始 evidence 排名。正题按题宏平均；负题单独统计；没有某类题时指标为 null。缺失、废止、解析失败或版本错误的金标依据直接报错，避免误报为算法失败。

默认运行：`.\.venv\Scripts\python.exe -m evaluation.run`。真实快照：加 `--mode real --database <合法资料库SQLite> --dataset <人工金标JSON>`。真实评测库应不含现行 DEMO；当前离线基线要求 local 哈希向量，与生产 embedding_id 一致。不会调用远程 API，不会写聊天记录。报告不包含原文和绝对源文件路径，但可能包含保密问题和规范元数据，应自行保护，不提交动态 reports/。

Debug bonus 字段是乘数（1 表示无加权）：Final = RRF × completeness × standard number × category，然后保留 6 位小数。候选仍需满足 overlap >= 0.12、BM25 > 0、指定编号等既有门槛。
