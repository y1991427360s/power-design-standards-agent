KS = (1, 3, 5, 10)


def matches(row, target, clause=False):
    return (row['standard_code'] == target.standard_code and row['version'] == target.version
            and (not clause or row['clause'] == target.clause))


def ranking_metrics(rows, groups, clause=False):
    """Hit: any relevant item. Recall: fraction of required groups covered.

    Document rankings must be deduplicated by caller; MRR uses first relevant rank.
    """
    if not groups:
        raise ValueError('Metrics require targets')
    rows = rows[:max(KS)]
    ranks = [next((i for i, row in enumerate(rows, 1)
                   if any(matches(row, t, clause) for t in group)), None) for group in groups]
    return {**{f'hit@{k}': float(any(r is not None and r <= k for r in ranks)) for k in KS},
            **{f'recall@{k}': sum(r is not None and r <= k for r in ranks)/len(groups) for k in KS},
            'mrr': 1/min(r for r in ranks if r is not None) if any(r is not None for r in ranks) else 0.0}


def document_ranking(rows):
    seen, result = set(), []
    for row in rows:
        key = (row['standard_code'], row['version'])
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result
