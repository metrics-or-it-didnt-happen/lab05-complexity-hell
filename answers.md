# Lab 05 - Answers

Analysis target: [`psf/requests`](https://github.com/psf/requests) (submodule at `oss/requests`),
analysed path `oss/requests/src/`.

## Task 1: radon vs lizard

### Summary of results

| Tool   | Functions/methods | Mean CC | Max CC | Warnings (CC > 10) |
|--------|------------------:|--------:|-------:|-------------------:|
| radon  |               233 |    3.45 |     21 |                 13 |
| lizard |               240 |    3.4  |     21 |                 13 |

Radon excludes classes from the unit count (we skip them too, since their CC is
just the sum of their methods). Lizard counts every definition - including class
bodies that act as namespaces - which explains the slightly higher function count.

### Q1: Do both tools agree on the "worst" function?

Yes - both tools pick `RequestEncodingMixin._encode_files`
(`src/requests/models.py:139`) as the single most complex unit, with
**CC = 21** in radon and **CCN = 21** in lizard. The top-10 lists overlap almost
completely: both flag `_encode_files`, `HTTPAdapter.send`, `build_digest_header`,
`prepare_url`, `prepare_body`, `should_bypass_proxies`, `resolve_redirects`,
`cert_verify`, `_encode_params`, `Session.send`, `get_netrc_auth` and
`guess_json_utf`. The ordering differs only where CC is tied.

### Q2: Are CC values identical? If not, why?

They mostly agree, but there is one visible discrepancy in the top-20:

| Function      | radon CC | lizard CCN | diff |
|---------------|---------:|-----------:|-----:|
| `super_len`   |       18 |         16 |   +2 |

**Cause:** radon counts each boolean operator in a condition
(`and`, `or`) as an extra decision point; lizard's McCabe implementation does
**not** by default. The body of `super_len` contains exactly two compound
conditions:

```python
if not is_urllib3_1 and isinstance(o, str):
if hasattr(o, "seek") and total_length is None:
```

Two `and`s → +2 in radon, nothing in lizard → the observed 18 vs 16 gap.

This is a known difference in how the two tools implement McCabe's original
metric. Radon follows the "extended" McCabe rule (short-circuit boolean
operators add independent paths because they can cause different execution
outcomes), lizard follows the stricter "structural" rule (only control-flow
statements count).

### Q3: Which tool gives more information?

Different angles rather than more / less:

- **radon** groups output by file, gives a rank (A-F) per unit, produces a
  clean JSON payload (`radon cc -j`), and has a separate Maintainability Index
  command (`radon mi`). Its rank thresholds make it the natural choice for the
  profiler in Task 2.
- **lizard** is multi-language (C/C++, Java, Go, JS, ...), prints NLOC, token
  count, parameter count and function length alongside CC, and offers
  immediately useful CSV output (`lizard --csv`). For a mixed-language code
  base it is the more general tool.

For this lab (Python-only) radon is the better fit because of the A-F ranking
and JSON shape. Lizard is the better pick when analysing a project in several
languages or when parameter count / function length matter as much as CC.

### Q4: Is the "worst" function really as complex as the metric says?

`RequestEncodingMixin._encode_files` (CC = 21, rank D) really does deserve
attention, but not because it is pathologically branchy - it is a two-phase
builder for multipart/form-data bodies:

1. **Normalisation phase** - the outer `for field, val in fields` loop walks
   the supplied `data` dict/tuples, coerces each value to bytes, and appends
   it to `new_fields`. It is nested 3 levels deep (`for`, `for`, `if`) with
   extra `if/elif` branches for the `bytes` vs `str` cases - this alone
   contributes ~9 CC.

2. **File-attachment phase** - the second `for k, v in files` loop decodes the
   file specification, which can be a bare file-like object, a 2-, 3-, or
   4-tuple, and branches further on `str/bytes/bytearray` vs `hasattr(fp, "read")`
   vs `None`. Another ~9 CC.

Plus the two guard clauses at the top and the final call to
`encode_multipart_formdata` - total ~21, which matches.

**Verdict:** the function does too many things at once (argument-shape
normalisation + file-handle normalisation + multipart encoding). CC = 21 is a
fair signal. A straightforward refactor would split it into
`_normalise_data_fields(data)`, `_normalise_file_field(k, v)` and a small
orchestrator - each piece well under CC = 10. The metric is not crying wolf
here; it correctly points at a function that has outgrown its single
responsibility.

## Statistics (for reference)

From `complexity_profiler.py oss/requests/src/`:

```
Functions/methods:   233
Mean CC:             3.45
Median CC:           2.0
Stdev CC:            3.71
Max CC:              21
Functions CC > 10:   13 (5.6%)

Rank distribution:
  A (1-5):    188 (80.7%)
  B (6-10):    32 (13.7%)
  C (11-20):   12  (5.2%)
  D (21-30):    1  (0.4%)
  E (31-40):    0  (0.0%)
  F (41+):      0  (0.0%)
```

Healthy profile overall: ~95% of functions fall in rank A or B, and there are
no E/F outliers. The 13 rank-C/D functions are the natural refactoring
candidates and cluster in `models.py`, `utils.py`, `adapters.py` and
`sessions.py` - exactly the hot-spot modules for a HTTP library.
