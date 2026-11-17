# Decathalon datalist loader

## Goals
- Provide a public loader for Medical Segmentation Decathlon datalist JSON files that returns per-case items with paths resolved against a base directory.

## Scope
- In scope: one public loader function, its module, its monai.data export, a docs entry, and a unit test module.
- Out of scope: training code, transforms, dataset classes, utility changes, dependencies, and datalist writers.

## Workflows
Run in order; raise ValueError at the first failed check.
1. Check that data_list_file_path names an existing file before opening it.
2. Open the file and parse it as JSON.
3. Check that the top-level object contains data_list_key, then take its value as the entry list.
4. If data_list_key equals "test", wrap each entry as an item whose only field is "image", regardless of is_segmentation and before validation.
5. If base_dir is None, use the directory portion of data_list_file_path, without making it absolute.
6. For each item, in order:
   a. The item must be a mapping.
   b. Resolve "image".
   c. Resolve "label" only when is_segmentation is true; otherwise leave it as stored.
   d. Leave other fields unchanged. Missing "image" or "label" is not an error.
7. Resolve a path value:
   - A string is joined with base_dir and normalized (collapse "." and redundant separators). An absolute string stays absolute.
   - A list: every element must be a string, resolved independently, never joined. Keep length and order.
   - Any other type is an error.
8. Return processed items in original order.

## Data model
- Non-"test" entries are objects. "image" is a string or list of strings. "label" is a string or list of strings in segmentation mode; in classification mode it may be any JSON value, such as an integer class id. Extra fields are kept verbatim.
- "test" entries are plain path strings.
- Output: a list of objects with the input field names; "image", and "label" in segmentation mode, hold resolved paths.

## API contracts
- Public function load_decathalon_datalist, spelled "Decathalon" to match the reference, importable as monai.data.load_decathalon_datalist.
- Parameters in order: data_list_file_path (string, required); is_segmentation (boolean, default true); data_list_key (string, default "training"); base_dir (optional string, default none, meaning the datalist file's directory).
- Type hints are optional. If present, they must cover all four parameters and the return, with base_dir typed as an optional string. Do not mix annotated and unannotated parameters.
- Errors: ValueError for every validation condition, never FileNotFoundError.

## Module architecture
- Place the loader in monai/data/decathalon_dataloader.py, as in the reference.
- Import the public name explicitly in monai/data/__init__.py, because the wildcard import from utils does not guarantee it.
- Docs: in docs/source/data.rst, after the existing Utilities automodule entry, add subsection "Decathalon DataLoader" underlined with tildes, nested under Utilities, with one autofunction entry for monai.data.load_decathalon_datalist.
- Do not import from other monai packages.

## Implementation constraints
- Standard library only (os and json). Do not change requirements, setup files, or existing functions in monai/data/utils.py.
- Keep file access and JSON parsing inside the loader.

## Naming
- Test module tests/test_load_decathalon_datalist.py, containing class TestLoadDecathalonDatalist. Use "decathalon" consistently in names, docs, and test identifiers.
- The only new public name is the loader; helpers use a leading underscore.

## Validation
- Missing datalist file: ValueError naming the file.
- Missing data_list_key: ValueError naming the key and file.
- Non-mapping item: ValueError.
- "image" values, and "label" values in segmentation mode, must be a string or list of strings, with element types checked inside lists. Classification labels are not type-checked.
- Do not coerce values to strings or swallow exceptions. Raise only ValueError, with f-string messages naming the offending file, key, or value.

## Documentation
- Google-style docstring like those in monai/data/utils.py, with each Args entry written "name (type): description". Describe the is_segmentation label behavior and the data_list_key and base_dir defaults.
- Describe the return shape in prose; a short example is allowed.

## Compatibility
- Additive only. Existing monai.data names, signatures, and behaviors are unchanged. Must run on Python 3.9.

## Maintainability
- Black-format the loader module, the export line, and the test module at line length 120, as runtests.sh checks with black and flake8. If black is absent, measure line lengths.
- Split any bracketed list or call over 120 columns one element per line with a trailing comma, including test literals and docstrings.

## Behavioral acceptance criteria
- Classification: an integer label stays the same integer.
- base_dir omitted: relative values resolve against the datalist's directory; absolute values stay absolute.
- A string in a non-path field is not path-joined.
- The default "training" key on a "test"-only datalist is a missing-key ValueError.

## Test requirements
- Import the public name from monai.data. Class TestLoadDecathalonDatalist has four tests. Every call passes the key and base_dir explicitly; the key must exist in that test's datalist.
  - test_seg_values: segmentation, training key, base_dir supplied; image and label resolved using scalar string paths, as the reference does.
  - test_cls_values: classification; integer labels stay integers; images resolved.
  - test_seg_no_basedir: base_dir none, training key; absolute image and label paths preserved. Build absolute inputs by joining the temporary directory with each file name, never hardcoding separators, because CI runs on Windows, Linux, and macOS.
  - test_seg_no_labels: only a "test" key with plain string entries; segmentation at its default; base_dir supplied; first item's image resolved.
- Build expectations with the loader's path-joining approach so they compare equal on every platform.
- Each test removes its temporary directory in all outcomes.
- Do not assert the old bare-string return for "test", or a ValueError for label-less items.
- Include the MONAI license header, use unittest, follow PEP 8 blank-line rules, and end with the standard main guard.
