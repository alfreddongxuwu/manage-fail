

from __future__ import annotations

from collections import defaultdict
import math
from statistics import mean, variance
from typing import Callable, Iterable, Mapping, Sequence

MAIN_CONDITIONS = ("item", "prior", "qud", "utterance_id")
NORMING_CONDITIONS = ("item", "prior")

def _condition_values(records, value_key, condition_keys):
    cells = defaultdict(list)
    for row in records:
        value = value_key(row) if callable(value_key) else row.get(value_key)
        if value in (None, ""):
            continue
        value = float(value)
        if not math.isfinite(value):
            continue
        key = tuple(row[key] for key in condition_keys)
        cells[key].append(value)
    return dict(cells)

def condition_means(records, value_key, condition_keys=MAIN_CONDITIONS):

    return {key: mean(values) for key, values in
            _condition_values(records, value_key, condition_keys).items()}

def condition_mean(records, value_key, condition_keys=MAIN_CONDITIONS):

    cells = condition_means(records, value_key, condition_keys)
    if not cells:
        raise ValueError("Cannot average an empty set of condition means")
    return mean(cells.values())

def summarize_conditions(records, value_key, condition_keys=MAIN_CONDITIONS):

    cells = _condition_values(records, value_key, condition_keys)
    if not cells:
        return dict(n=0, n_cells=0, mean=None, sd=None, se=None, df=None,
                    min=None, max=None)
    count = len(cells)
    means = [mean(values) for values in cells.values()]
    center = mean(means)
    all_values = [v for values in cells.values() for v in values]
    result = dict(n=len(all_values), n_cells=count, mean=center, sd=None,
                  se=None, df=None, min=min(all_values), max=max(all_values))
    if any(len(values) < 2 for values in cells.values()):
        return result
    variances = [variance(values) for values in cells.values()]
    contributions = [var / len(values) / count**2
                     for var, values in zip(variances, cells.values())]
    total_var = sum(contributions)
    denominator = sum(component**2 / (len(values)-1)
                      for component, values in zip(contributions, cells.values()))
    result.update(
        sd=math.sqrt(mean(var + (cell_mean-center)**2
                          for var, cell_mean in zip(variances, means))),
        se=math.sqrt(total_var),
        df=total_var**2 / denominator if denominator > 0 else math.inf,
    )
    return result
