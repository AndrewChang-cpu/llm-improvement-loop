# Decathalon datalist loader

## Goals
- Provide a public loader that reads a Medical Segmentation Decathlon style datalist JSON file and returns per-case items with image and label paths resolved against a base directory, for segmentation or classification.
- The feature is additive and not a breaking change.

## Scope
- In scope: one public loader function, a loader module in monai/data, its export from monai.data, a docs entry, and a unit test module.
- Out of scope: training code, transforms, dataset classes, changes to existing monai.data utilities, new dependencies, and datalist writing tools.

## Workflows
Run these steps in order. Raise ValueError at the first failed check.
1. Check that data_list_file_path names an existing file before opening it, so a missing file never reaches the file-open call.
2. Open the file and parse it as JSON.
3. Check that the top-level object contains data_list_key. A datalist with only a "test" key fails here under the default "training" key.
4. Take the value under data_list_key as the list of entries.
5. If data_list_key equals "test", convert each entry into an item whose only field is "image" holding the entry. This applies regardless of is_segmentation and happens before validation or path resolution.
6. If base_dir is None, use the directory portion of data_list_file_path, without converting it to an absolute path.
7. For each item, in order:
   a. The item must be a mapping.
   b. Resolve field "image".
   c. Resolve field "label" only when is_segmentation is true. When false, leave the label exactly as stored, whatever its type.
   d. Leave all other fields unchanged, including string fields outside "image" and "label".
   e. A missing "image" or "label" is not an error. Add no presence check for either field.
8. Resolve a path value:
   - A string: join it with base_dir and normalize the result (collapse "." and redundant separators). An absolute string stays absolute.
   - A list: every element must be a string, resolved independently as a complete path exactly as a single string. Elements are never joined to each other. The result keeps the length and order of the input.
   - Any other type is an error.
9. Return the processed items in the original order.

## Data model
- Input: a JSON object. Entries live under data_list_key; other top-level fields are ignored.
- Entries under a non-"test" key are objects. "image" is a string or a list of strings. "label" is a string or a list of strings when is_segmentation is true; when false it may be any JSON value, such as an integer class id. Extra fields are preserved verbatim.
- Entries under "test" are plain path strings, converted to image-only items (step 5).
- Output: a list of objects with the input field names. "image" and, in segmentation mode, "label" hold resolved paths, as a string or as a list of the same length and order.

## API contracts
- Public function name: load_decathalon_datalist. Keep the spelling "decathalon" to match the reference. It must be importable as monai.data.load_decathalon_datalist.
- Parameters, in order:
  - data_list_file_path (string path to the JSON datalist). Required.
  - is_segmentation (boolean), default true.
  - data_list_key (string), default "training".
  - base_dir (optional string), default none, meaning the datalist file's directory.
- Type hints are optional. If used, they must cover all parameters and the return, typing base_dir as an optional string. Do not mix annotated and unannotated parameters.
- Return: a list of objects as described in Data model.
- Errors: ValueError for every condition under Validation. Never raise FileNotFoundError for a missing datalist.

## Module architecture
- Place the loader in a dedicated module in monai/data, named decathalon_dataloader as in the reference. Helpers stay private to that module.
- Register the public name with an explicit import in monai/data/__init__.py, because the existing wildcard import from utils does not guarantee it.
- Docs: in docs/source/data.rst, after the existing Utilities automodule entry, add a subsection titled "Decathalon DataLoader" underlined with tildes so it nests under Utilities. It holds one autofunction entry for monai.data.load_decathalon_datalist.
- Layering: the loader imports no other monai package.

## Implementation constraints
- Standard library only (os and json). Do not change requirements or setup files.
- Keep file access and JSON parsing inside the loader. Do not change existing functions in monai/data/utils.py.
- Path resolution is one private helper, used only for "image" and, in segmentation mode, "label". It handles the string case; the list case applies it to each element.

## Naming
- Test module: tests/test_load_decathalon_datalist.py, containing class TestLoadDecathalonDatalist. Use "decathalon" consistently in names, docs, and test identifiers.
- Helpers use a leading underscore. The only new public name is the loader.

## Validation
- Missing datalist file: ValueError naming the file.
- Missing data_list_key: ValueError naming the key and the file.
- Non-mapping item: ValueError.
- "image" values, and "label" values in segmentation mode, must be a string or a list of strings, with element types checked inside lists.
- Classification labels (is_segmentation false) are not type-checked.
- Do not coerce values to strings. A wrongly typed value is an error, not a silently converted path.
- Raise ValueError only, never another exception type, and do not catch and swallow exceptions inside the loader. Messages are f-strings naming the offending file, key, or value, matching repository style.

## Documentation
- The public function has a Google-style docstring like those in monai/data/utils.py. Its Args block lists each entry as "name (type): description", even when the signature has type hints. Describe the is_segmentation label behavior and the data_list_key and base_dir defaults.
- Describe the return value in a prose paragraph giving its shape. A short example block is allowed.

## Compatibility
- Additive only. Existing monai.data names, signatures, and behaviors are unchanged. Must run on Python 3.9, the recorded environment.

## Maintainability
- Gate: runtests.sh runs black and flake8. The loader module, the export line, and the test module must be black-formatted at line length 120.
- Keep statements and literals that fit in 120 columns on one line. Split longer bracketed lists or calls one element per line with a trailing comma, including test datalist literals and docstrings. Black may not be installed, so measure line lengths directly.

## Behavioral acceptance criteria
- Segmentation, training key, base_dir supplied: image and label resolve to normalized paths under base_dir in list order, and extra fields are kept.
- A two-element list of relative strings never becomes one element or one combined path.
- Classification, training key, integer label: image resolves and the label stays the same integer.
- The default "training" key on a datalist with only a "test" key is a missing-key ValueError. This is expected, not a defect to work around.

## Test requirements
- The test module imports the public name from monai.data and contains class TestLoadDecathalonDatalist with four tests. Every call passes the datalist key and base_dir explicitly, and the key must exist in that test's datalist.
  - test_seg_values: segmentation, training key, base_dir supplied; image and label resolved. Use scalar string paths, as the reference does.
  - test_cls_values: classification, integer labels stay integers, images resolved.
  - test_seg_no_basedir: base_dir none, training key; absolute image and label paths preserved. Build absolute inputs by joining the temporary directory with each file name. Do not hardcode a path separator, drive-less root, or leading slash, because CI runs on Windows, Linux, and macOS.
  - test_seg_no_labels: the datalist has only a "test" key with plain string entries. Pass "test" explicitly. Segmentation at its default, base_dir supplied, first item's image resolved.
- Build expectations with the loader's path-joining approach so they compare equal on every platform.
- Each test creates its temporary directory and removes it in all outcomes.
- Do not assert the old bare-string return for the "test" key, or a ValueError for label-less items.
- Include the MONAI license header, use unittest, follow PEP 8 blank-line rules, and end with the standard main guard.
