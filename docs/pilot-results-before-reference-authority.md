# Pilot results

Status: held after Sphinx revision three while resolving contradictory baseline/reference contracts. Baseline inputs are the original PR titles and descriptions verbatim. All runs use GPT-6 Luna. The tables below distinguish judge-reported criterion failures from observed executable test failures.

## Evaluation reliability

Full-run failures are supported by executed tests. Qualitative diagnoses require review. In the Sphinx baseline, at least one judge demanded `allow_nesting=True` for alias directives. The reference `PyTypeAlias` does not set that flag; nesting an alias inside a class uses the surrounding class context. This is an unsupported diagnostic requirement, even though the affected run still fails actual tests.

Sphinx PR #11989 describes the optional alias expression using the `value` option; the merged code and reference tests use `canonical`. The baseline follows the former while evaluation uses the latter. This interface mismatch contributes to the repeated failures and limits interpretation of any improvement as purely improved architectural instructions.

Direct inspection of the reference confirms that `PyTypeAlias` accepts `canonical`, does not accept `value`, and has `allow_nesting=False`. Revision three produced two patches passing all reference tests, but both were rejected for not implementing the original PR description's `value` option. The next editor output then switched back to `value`, demonstrating oscillation between two conflicting targets. An authoritative-contract rule must be fixed before the results can be interpreted.

Results are exploratory pilot observations. Codex review of judgments is an additional automated review, not human validation. The human-audit sample will remain unfilled until a human reviews it.

## sphinx-doc__sphinx-11989

### revision-00

Full passes: **0/10**.

Judge-reported failures:

| Criterion | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `api_contract` | 10/10 |
| `convention_fit` | 10/10 |
| `requirement_intent` | 10/10 |
| `extension_point_adherence` | 8/10 |
| `architectural_fit` | 4/10 |

Observed test failures:

| Test | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 9/10 |
| Collection error: `tests/test_domains/test_domain_py.py` | 1/10 |

Full artifacts: `.experiments/results/sphinx-doc__sphinx-11989/revision-00`.

### revision-01

Full passes: **0/10**.

Judge-reported failures:

| Criterion | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `api_contract` | 9/10 |
| `extension_point_adherence` | 3/10 |
| `convention_fit` | 10/10 |
| `requirement_intent` | 10/10 |

Observed test failures:

| Test | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 9/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 1/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 1/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 1/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 1/10 |
| Collection error: `tests/test_domains/test_domain_py.py` | 1/10 |

Full artifacts: `.experiments/results/sphinx-doc__sphinx-11989/revision-01`.

### revision-02

Full passes: **0/10**.

Judge-reported failures:

| Criterion | Failed runs |
| --- | ---: |
| `patch_and_checks` | 10/10 |
| `requirement_intent` | 10/10 |
| `convention_fit` | 9/10 |
| `api_contract` | 5/10 |
| `extension_point_adherence` | 1/10 |

Observed test failures:

| Test | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 9/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 9/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 2/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_pydata_signature` | 1/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_pydata_signature_old` | 1/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_pydata_with_union_type_operator` | 1/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_pydata` | 1/10 |
| Collection error: `tests/test_domains/test_domain_py.py` | 1/10 |

Full artifacts: `.experiments/results/sphinx-doc__sphinx-11989/revision-02`.


### revision-03

Full passes: **0/10**. Two runs pass all executable checks but fail subjective judgments against the conflicting PR option name.

Judge-reported failures:

| Criterion | Failed runs |
| --- | ---: |
| `api_contract` | 9/10 |
| `convention_fit` | 9/10 |
| `requirement_intent` | 9/10 |
| `patch_and_checks` | 8/10 |
| `extension_point_adherence` | 3/10 |
| `architectural_fit` | 2/10 |

Observed test failures:

| Test | Failed runs |
| --- | ---: |
| `tests/test_domains/test_domain_py_pyobject.py::test_py_type_alias` | 8/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_xrefs_abbreviations` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_objects` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_resolve_xref_for_properties` | 2/10 |
| `tests/test_domains/test_domain_py.py::test_domain_py_find_obj` | 2/10 |
| `tests/test_domains/test_domain_py_pyobject.py::test_domain_py_type_alias` | 2/10 |
