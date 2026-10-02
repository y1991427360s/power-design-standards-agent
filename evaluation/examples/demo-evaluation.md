# RAG evaluation

DEMO flow validation only

Document metrics use deduplicated document ranks. Clause metrics use evidence ranks.
Hit means any correct target; Recall measures required groups covered; MRR is truncated at 10.
Keyword labels are diagnostic only, never substitutes for evidence.

document hit@1: 1.0000
document hit@3: 1.0000
document hit@5: 1.0000
document hit@10: 1.0000
document recall@1: 0.8889
document recall@3: 1.0000
document recall@5: 1.0000
document recall@10: 1.0000
document mrr: 1.0000
clause hit@1: 1.0000
clause hit@3: 1.0000
clause hit@5: 1.0000
clause hit@10: 1.0000
clause recall@1: 0.8889
clause recall@3: 1.0000
clause recall@5: 1.0000
clause recall@10: 1.0000
clause mrr: 1.0000
total_questions: 12
positive_questions: 9
negative_questions: 3
negative_rejection_accuracy: 1.0
negative_false_formal_rate: 0.0

## SEC-001: 控制电缆屏蔽层应如何接地？

Expected: {"documents": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": null}], "clauses": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": "3.2.1"}], "groups": []}

Outcome: {"document": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "clause": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "failed": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
|1|DEMO-001 / 2026 测试版|3.2.1|10.3696|0.5335|0.032787|1.08|1.0|0.03541|
|2|DEMO-002 / 2026 测试版|3.2.1|5.9754|0.4091|0.032258|1.08|1.0|0.034839|
|3|DEMO-001 / 2026 测试版|3.2.2|1.8977|0.1448|0.031746|1.08|1.0|0.034286|

## SEC-002: 控制电缆备用芯应如何编号？

Expected: {"documents": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": null}], "clauses": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": "3.2.2"}], "groups": []}

Outcome: {"document": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "clause": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "failed": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
|1|DEMO-001 / 2026 测试版|3.2.2|10.8248|0.3862|0.032787|1.08|1.0|0.03541|
|2|DEMO-002 / 2026 测试版|3.2.1|1.9978|0.0909|0.032002|1.08|1.0|0.034562|
|3|DEMO-001 / 2026 测试版|3.2.1|1.9299|0.1334|0.032002|1.08|1.0|0.034562|

## SEC-003: DEMO-001 和 DEMO-002 对控制电缆屏蔽层分别怎么规定？

Expected: {"documents": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": null}, {"standard_code": "DEMO-002", "version": "2026 测试版", "clause": null}], "clauses": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": "3.2.1"}, {"standard_code": "DEMO-002", "version": "2026 测试版", "clause": "3.2.1"}], "groups": []}

Outcome: {"document": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 0.5, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "clause": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 0.5, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "failed": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
|1|DEMO-001 / 2026 测试版|3.2.1|7.9382|0.4055|0.032787|1.08|1.3|0.046033|
|2|DEMO-002 / 2026 测试版|3.2.1|6.8663|0.3769|0.032258|1.08|1.3|0.04529|
|3|DEMO-001 / 2026 测试版|3.2.2|2.7439|0.1601|0.031746|1.08|1.3|0.044571|

## SEC-004: DEMO-002 屏蔽层连接位置如何记录？

Expected: {"documents": [{"standard_code": "DEMO-002", "version": "2026 测试版", "clause": null}], "clauses": [{"standard_code": "DEMO-002", "version": "2026 测试版", "clause": "3.2.1"}], "groups": []}

Outcome: {"document": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "clause": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "failed": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
|1|DEMO-002 / 2026 测试版|3.2.1|10.6956|0.585|0.032787|1.08|1.3|0.046033|

## SEC-005: 电流互感器二次回路接线前需要核对什么？

Expected: {"documents": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": null}], "clauses": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": "6.1.1"}], "groups": []}

Outcome: {"document": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "clause": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "failed": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
|1|DEMO-001 / 2026 测试版|6.1.1|10.4152|0.3508|0.032787|1.08|1.0|0.03541|

## SEC-006: CT 二次接线前咋检查极性标记？

Expected: {"documents": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": null}], "clauses": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": "6.1.1"}], "groups": []}

Outcome: {"document": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "clause": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "failed": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
|1|DEMO-001 / 2026 测试版|6.1.1|10.7932|0.4|0.032787|1.08|1.0|0.03541|

## SEC-007: 控制缆线备用芯编号与接线图有什么关系？

Expected: {"documents": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": null}], "clauses": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": "3.2.2"}], "groups": []}

Outcome: {"document": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "clause": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "failed": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
|1|DEMO-001 / 2026 测试版|3.2.2|12.0843|0.3884|0.032787|1.08|1.0|0.03541|
|2|DEMO-002 / 2026 测试版|3.2.1|1.9978|0.1097|0.032002|1.08|1.0|0.034562|
|3|DEMO-001 / 2026 测试版|3.2.1|1.9299|0.143|0.032002|1.08|1.0|0.034562|

## SEC-008: 控制电缆屏蔽层和 CT 二次回路测试有哪些要求？

Expected: {"documents": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": null}], "clauses": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": "3.2.1"}, {"standard_code": "DEMO-001", "version": "2026 测试版", "clause": "6.1.1"}], "groups": []}

Outcome: {"document": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "clause": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 0.5, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "failed": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
|1|DEMO-001 / 2026 测试版|3.2.1|7.98|0.4518|0.032787|1.08|1.0|0.03541|
|2|DEMO-001 / 2026 测试版|6.1.1|7.1693|0.3354|0.032002|1.08|1.0|0.034562|
|3|DEMO-002 / 2026 测试版|3.2.1|6.9015|0.4264|0.032002|1.08|1.0|0.034562|
|4|DEMO-001 / 2026 测试版|3.2.2|2.9736|0.2642|0.031250|1.08|1.0|0.03375|

## SEC-009: 控制电缆屏蔽层测试要求

Expected: {"documents": [{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": null}, {"standard_code": "DEMO-002", "version": "2026 测试版", "clause": null}], "clauses": [], "groups": [[{"standard_code": "DEMO-001", "version": "2026 测试版", "clause": "3.2.1"}, {"standard_code": "DEMO-002", "version": "2026 测试版", "clause": "3.2.1"}]]}

Outcome: {"document": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 0.5, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "clause": {"hit@1": 1.0, "hit@3": 1.0, "hit@5": 1.0, "hit@10": 1.0, "recall@1": 1.0, "recall@3": 1.0, "recall@5": 1.0, "recall@10": 1.0, "mrr": 1.0}, "failed": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
|1|DEMO-001 / 2026 测试版|3.2.1|7.98|0.6061|0.032787|1.08|1.0|0.03541|
|2|DEMO-002 / 2026 测试版|3.2.1|6.9015|0.5721|0.032258|1.08|1.0|0.034839|
|3|DEMO-001 / 2026 测试版|3.2.2|2.9736|0.3545|0.031746|1.08|1.0|0.034286|

## NEG-001: 月球核聚变反应堆安全距离是多少？

Expected: {"documents": [], "clauses": [], "groups": []}

Outcome: {"rejected": true, "false_formal_evidence": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
No retrieved evidence.

## NEG-002: GB 999999 对控制电缆屏蔽层有什么要求？

Expected: {"documents": [], "clauses": [], "groups": []}

Outcome: {"rejected": true, "false_formal_evidence": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
No retrieved evidence.

## NEG-003: 紫色端子标记备用芯是否属于规范要求？

Expected: {"documents": [], "clauses": [], "groups": []}

Outcome: {"rejected": true, "false_formal_evidence": false}

|Rank|Document / version|Clause|BM25|Vector|RRF|Completeness ×|Standard ×|Final|
|---|---|---|---|---|---|---|---|---|
|1|DEMO-001 / 2026 测试版|3.2.2|4.4964|0.0801|0.032787|1.08|1.0|0.03541|
