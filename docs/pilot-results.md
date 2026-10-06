# Corrected pilot results

Status: stopped. Revisions zero through five are complete; revision six has partial judgments because Codex reported a usage limit. Both reference-patch controls passed all eleven criteria and their executable checks. The filesystem policy and editor prompt have since changed; these recorded outcomes belong to the earlier restricted-access condition.

The reference implementation is authoritative for behavior, public contracts, and intended architecture. The original PR title and description supply only the baseline generation prompt. Judge inputs contain no PR-derived behavioral requirements; the editor receives the current editable draft rather than a separate immutable baseline.

Artifacts: `.experiments/reference-authority/`. Earlier results using conflicting contracts are retained in [the diagnostic report](pilot-results-before-reference-authority.md) and are excluded from this comparison. Protocol changes are recorded in [experiment-adjustments.md](experiment-adjustments.md).

All eleven criteria remain required. A run passes only when every criterion passes; convergence and confirmation each require at least nine of ten fresh runs. There are at most ten editor revisions after the baseline.

At each completed revision, report full pass counts, judge-reported criterion failures, and observed executable test failures. Codex review of sampled judgments is additional automated review, not human validation.

## Batch outcomes

### sphinx-doc__sphinx-11989/revision-00

Full passes: **0/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `api_contract` | 10/10 |
| `extension_point_adherence` | 8/10 |
| `convention_fit` | 10/10 |
| `requirement_intent` | 10/10 |
| `architectural_fit` | 1/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 5/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 5/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 5/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 2/10 |

Observed collection errors:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py` | 5/10 |

### sphinx-doc__sphinx-11989/revision-01

Full passes: **0/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `convention_fit` | 9/10 |
| `requirement_intent` | 8/10 |
| `api_contract` | 7/10 |
| `extension_point_adherence` | 1/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 7/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 7/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 7/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 7/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 7/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 10/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 8/10 |

Observed collection errors:

None.

### sphinx-doc__sphinx-11989/revision-02

Full passes: **0/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `api_contract` | 8/10 |
| `convention_fit` | 9/10 |
| `requirement_intent` | 9/10 |
| `extension_point_adherence` | 1/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 10/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 6/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 6/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 6/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 6/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 6/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 7/10 |

Observed collection errors:

None.

### sphinx-doc__sphinx-11989/revision-03

Full passes: **1/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `convention_fit` | 9/10 |
| `requirement_intent` | 8/10 |
| `patch_and_checks` | 5/10 |
| `api_contract` | 5/10 |
| `extension_point_adherence` | 1/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 4/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 4/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 4/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 4/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 4/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 5/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 4/10 |

Observed collection errors:

None.

### sphinx-doc__sphinx-11989/revision-04

Full passes: **1/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `convention_fit` | 9/10 |
| `patch_and_checks` | 8/10 |
| `api_contract` | 5/10 |
| `requirement_intent` | 8/10 |
| `extension_point_adherence` | 3/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 5/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 5/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 5/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 5/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 5/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 8/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 5/10 |

Observed collection errors:

None.

### sphinx-doc__sphinx-11989/revision-05

Full passes: **2/10**.

Judge-reported criterion failures:

| Item | Failed runs |
| --- | ---: |
| `convention_fit` | 8/10 |
| `patch_and_checks` | 6/10 |
| `api_contract` | 7/10 |
| `requirement_intent` | 7/10 |
| `extension_registration` | 1/10 |

Observed executable test failures:

| Item | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 6/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 3/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 3/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 3/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 3/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 3/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 3/10 |

Observed collection errors:

None.

