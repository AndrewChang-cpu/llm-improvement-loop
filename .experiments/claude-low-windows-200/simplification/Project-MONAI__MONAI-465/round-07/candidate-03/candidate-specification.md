# Decathalon datalist loader

## Scope
- In scope: a public loader for Medical Segmentation Decathlon datalist JSON files returning per-case items with resolved paths, its module, its monai.data export, a docs entry, and a unit test module.
- Out of scope: training code, transforms, dataset classes, utility changes, new dependencies, datalist writers.

## Workflows
Run in order; raise ValueError at the first failed check.
1. Confirm data_list_file_path names an existing file, then parse it as JSON.
2. Confirm the top-level object contains data_list_key; its value is the list of entries.
3. If data_list_key equals "test", wrap each entry as an item whose only field is "image", regardless of is_segmentation, before validation.
4. If base_dir is None, use the directory portion of data_list_file_path, without making it absolute.
5. For each item, in order: it must be a mapping; resolve "image"; resolve "label" only in segmentation mode, otherwise leave it as stored. Keep other fields unchanged. Neither key is required.
6. Resolve a path value:
   - A string is joined with base_dir and normalized; an absolute string stays absolute.
   - A list must contain only strings. Resolve each element independently, never joining; keep length and order.
   - Any other type is an error.
7. Return processed items in original order.

## Data model
- Non-"test" entries are objects. "image" and, in segmentation mode, "label" are strings or lists of strings. Classification labels may be any JSON value, such as an integer class id. Extra fields are kept verbatim.
- "test" entries are plain path strings.

## API contracts
- Public function load_decathalon_datalist (spelling matches the reference), importable as monai.data.load_decathalon_datalist.
- Parameters, in order: data_list_file_path (string, required); is_segmentation (boolean, default true); data_list_key (string, default "training"); base_dir (optional string, default none, meaning the datalist's directory).
- Type hints, if used, must cover all parameters and the return; never mix annotated and unannotated parameters.

## Module architecture
- Loader in monai/data/decathalon_dataloader.py, as in the reference.
- Import the public name explicitly in monai/data/__init__.py; the wildcard import from utils does not guarantee it.
- Docs: in docs/source/data.rst, after the Utilities automodule entry, add subsection "Decathalon DataLoader" underlined with tildes, holding one autofunction entry.
- Import nothing else from monai; use only os and json. Keep file access and JSON parsing in the loader. Leave requirements, setup files, and monai/data/utils.py unchanged. Helpers start with an underscore.
- Test module tests/test_load_decathalon_datalist.py contains class TestLoadDecathalonDatalist. Use "decathalon" in all names and identifiers.

## Validation
- Missing datalist file: ValueError naming the file. Never raise FileNotFoundError.
- Missing data_list_key: ValueError naming the key and file, including a missing training key in a "test"-only datalist.
- Non-mapping item: ValueError.
- Image values and segmentation labels must be a string or list of strings, with list elements checked. Classification labels are not type-checked.
- Never coerce values to strings or swallow exceptions. Raise only ValueError, with f-string messages naming the offending file, key, or value.

## Documentation
- Google-style docstring like those in monai/data/utils.py. Args lists each entry as "name (type): description". Describe label behavior, defaults, and return shape.

## Compatibility
- Additive only; existing monai.data names, signatures, and behaviors are unchanged. Must run on Python 3.9.

## Maintainability
- Black-format the loader, export line, and tests at line length 120; runtests.sh checks them. Split any bracketed list or call over 120 columns one element per line with a trailing comma.

## Test requirements
- Import the public name from monai.data. Each call passes the key and base_dir explicitly.
  - test_seg_values: segmentation, training key, base_dir supplied; image and label resolved.
  - test_cls_values: classification; integer labels stay integers; images resolved.
  - test_seg_no_basedir: base_dir none; absolute image and label paths preserved. Build absolute inputs by joining the temporary directory with each file name, never hardcoding separators.
  - test_seg_no_labels: only a "test" key with plain string entries; segmentation at default; base_dir supplied; first item's image resolved.
- Build expectations with the loader's path-joining approach. Each test removes its temporary directory in all outcomes.
- Do not assert the old bare-string "test" return or a ValueError for label-less items.
- Include the MONAI license header, use unittest, follow PEP 8 blank lines, and end with the standard main guard.
