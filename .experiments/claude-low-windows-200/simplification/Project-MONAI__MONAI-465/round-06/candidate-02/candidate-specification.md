# Decathalon datalist loader

## Goals
- Provide a public loader for Medical Segmentation Decathlon style datalist JSON files that returns per-case items with resolved paths.

## Scope
- In scope: the loader function, its module, its monai.data export, a docs entry, and unit tests.
- Out of scope: training code, transforms, dataset classes, utility changes, new dependencies, and datalist writers.

## Workflows
Run in order; raise ValueError at the first failed check.
1. Check that data_list_file_path names an existing file, then parse it as JSON.
2. Check that the top-level object contains data_list_key; its value is the list of entries.
3. If data_list_key equals "test", wrap each entry as an item whose only field is "image", regardless of is_segmentation, before validation.
4. If base_dir is None, use the directory portion of data_list_file_path, without making it absolute.
5. For each item, in order: it must be a mapping; resolve "image"; resolve "label" only when is_segmentation is true; leave other fields unchanged. Do not check that "image" or "label" is present.
6. Resolve a path value:
   - A string is joined with base_dir and normalized (collapse "." and redundant separators). An absolute string stays absolute.
   - A list must contain only strings. Resolve each element independently; never join elements.
   - Any other type is an error.
7. Return processed items in original order.

## Data model
- Non-"test" entries are objects. "image" is a string or list of strings. "label" is a string or list of strings in segmentation mode; in classification mode it may be any JSON value, such as an integer class id. Extra fields are kept verbatim.
- "test" entries are plain path strings.
- Output: objects with the input field names; resolved "image" and, in segmentation mode, "label".

## API contracts
- Public function load_decathalon_datalist, spelled "Decathalon" to match the reference, importable as monai.data.load_decathalon_datalist.
- Parameters, in order: data_list_file_path (string, required); is_segmentation (boolean, default true); data_list_key (string, default "training"); base_dir (optional string, default none, meaning the datalist's directory).
- Type hints are optional; if used, cover all parameters and the return, without mixing annotated and unannotated parameters.

## Module architecture
- Place the loader in monai/data/decathalon_dataloader.py, as in the reference. Do not import from other monai packages.
- Import the public name explicitly in monai/data/__init__.py; the wildcard import from utils does not guarantee it.
- Docs: in docs/source/data.rst, after the Utilities automodule entry, add subsection "Decathalon DataLoader" underlined with tildes, nested under Utilities, holding one autofunction entry.
- Test module tests/test_load_decathalon_datalist.py, containing class TestLoadDecathalonDatalist. Use "decathalon" in all names, docs, and test identifiers.

## Implementation constraints
- Standard library only (os and json). Do not change requirements, setup files, or existing functions in monai/data/utils.py.
- Keep file access and JSON parsing inside the loader. The loader is the only new public name; helpers use a leading underscore.
- Additive only: existing monai.data names, signatures, and behaviors are unchanged. Must run on Python 3.9.

## Validation
- Missing datalist file: ValueError naming the file. Never raise FileNotFoundError.
- Missing data_list_key: ValueError naming the key and file. A "test"-only datalist without the training key triggers this.
- Non-mapping item: ValueError.
- "image" values, and "label" values in segmentation mode, must be a string or list of strings, with list elements checked. Classification labels are not type-checked.
- Never coerce values to strings. Raise only ValueError, with f-string messages naming the offending file, key, or value. Never swallow exceptions.

## Documentation
- Google-style docstring like those in monai/data/utils.py. Its Args block lists each entry as "name (type): description". Describe the is_segmentation label behavior, the defaults, and the return shape in prose.

## Maintainability
- Black-format the loader, the export line, and the test module at line length 120, as runtests.sh checks with black and flake8. If black is absent, measure line lengths.
- Split any bracketed list or call over 120 columns one element per line with a trailing comma.

## Test requirements
- Import the public name from monai.data. Each call passes the key and base_dir explicitly; the key must exist in that test's datalist.
  - test_seg_values: segmentation, training key, base_dir supplied; image and label resolved as scalar string paths, as the reference does.
  - test_cls_values: classification; integer labels stay integers; images resolved.
  - test_seg_no_basedir: base_dir none; absolute image and label paths preserved. Build absolute inputs by joining the temporary directory with each file name.
  - test_seg_no_labels: only a "test" key with plain string entries; pass "test" explicitly; segmentation at its default; base_dir supplied; first item's image resolved.
- Build expectations with the loader's path-joining approach. Each test creates and removes its temporary directory in all outcomes.
- Do not assert the old bare-string return for "test", or a ValueError for label-less items.
- Include the MONAI license header, use unittest, follow PEP 8 blank-line rules, and end with the standard main guard.
