# Decathalon datalist loader

## Goals
- Provide a public loader for Medical Segmentation Decathlon datalist JSON files that returns per-case items with paths resolved against a base directory.

## Scope
- In scope: the loader, its module, its monai.data export, a docs entry, and a unit test module.
- Out of scope: training code, transforms, dataset classes, utility changes, new dependencies, and datalist writers.

## Workflows
Run in order; raise ValueError at the first failed check.
1. Check that data_list_file_path names an existing file, then parse it as JSON.
2. Check that the top-level object contains data_list_key; its value is the list of entries.
3. If data_list_key equals "test", wrap each entry as an item whose only field is "image", regardless of is_segmentation, before validation.
4. If base_dir is None, use the directory portion of data_list_file_path, without making it absolute.
5. For each item, in order:
   a. The item must be a mapping.
   b. Resolve "image".
   c. Resolve "label" only when is_segmentation is true; otherwise leave it as stored.
   d. Leave other fields unchanged. Do not require "image" or "label".
6. Resolve a path value:
   - A string is joined with base_dir and normalized (collapse "." and redundant separators). Absolute strings stay absolute.
   - A list must contain only strings. Resolve each element independently, never joining elements. Keep length and order.
   - Any other type is an error.
7. Return processed items in original order.

## Data model
- Non-"test" entries are objects. "image" is a string or list of strings. In segmentation mode, "label" is a string or list of strings; in classification mode it may be any JSON value, such as an integer class id. Extra fields are kept verbatim.
- "test" entries are plain path strings.

## API contracts
- Public function load_decathalon_datalist ("Decathalon" matches the reference), importable as monai.data.load_decathalon_datalist.
- Parameters, in order: data_list_file_path (string, required); is_segmentation (boolean, default true); data_list_key (string, default "training"); base_dir (optional string, default none, meaning the datalist's directory).
- Type hints are optional. If used, they must cover every parameter and the return. Do not mix annotated and unannotated parameters.

## Module architecture
- Loader in monai/data/decathalon_dataloader.py, as in the reference.
- Import the public name explicitly in monai/data/__init__.py; the wildcard import from utils does not guarantee it.
- Docs: in docs/source/data.rst, after the Utilities automodule entry, add subsection "Decathalon DataLoader" underlined with tildes, nested under Utilities, holding one autofunction entry.

## Implementation constraints
- Standard library only (os and json). Import no other monai packages. Do not change requirements, setup files, or existing functions in monai/data/utils.py.
- Keep file access and JSON parsing inside the loader. The loader is the only new public name; helpers use a leading underscore.

## Validation
- Missing datalist file: ValueError naming the file. Never raise FileNotFoundError.
- Missing data_list_key: ValueError naming the key and file. A missing training key on a "test"-only datalist is this error.
- Non-mapping item: ValueError.
- "image" values, and "label" values in segmentation mode, must be a string or list of strings, with list elements checked. Classification labels are not type-checked.
- Never coerce values to strings. Raise only ValueError, with f-string messages naming the offending file, key, or value.

## Documentation
- Google-style docstring like monai/data/utils.py. Its Args block lists each entry as "name (type): description", even with type hints. Describe the is_segmentation label behavior, defaults, and return shape.

## Compatibility
- Additive only; existing monai.data names, signatures, and behaviors are unchanged. Must run on Python 3.9.

## Maintainability
- Black-format the loader, export line, and test module at line length 120, as runtests.sh checks with black and flake8. Split any bracketed list or call over 120 columns one element per line with a trailing comma.

## Naming
- Test module tests/test_load_decathalon_datalist.py, class TestLoadDecathalonDatalist. Use "decathalon" in all names, docs, and identifiers.

## Test requirements
- Import the public name from monai.data. Pass the key and base_dir explicitly; the key must exist in that test's datalist.
  - test_seg_values: segmentation, training key, base_dir supplied; image and label resolved as scalar string paths.
  - test_cls_values: classification; integer labels stay integers; images resolved.
  - test_seg_no_basedir: base_dir none; absolute image and label paths preserved. Build absolute inputs by joining the temporary directory with each file name, with no hardcoded separators, since CI runs on Windows, Linux, and macOS.
  - test_seg_no_labels: only a "test" key with plain string entries; pass "test" explicitly; segmentation at default; first item's image resolved.
- Build expectations with the loader's path-joining approach so they match on every platform.
- Each test removes its temporary directory in all outcomes.
- Do not assert the old bare-string "test" return or a ValueError for label-less items.
- Include the MONAI license header, use unittest, follow PEP 8, and end with the main guard.
