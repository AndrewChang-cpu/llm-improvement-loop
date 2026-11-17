# Decathalon datalist loader

## Goals
- Provide a public loader that reads a Medical Segmentation Decathlon style datalist JSON file and returns per-case items with image and label paths resolved against a base directory.
- The feature is additive and not a breaking change.

## Scope
- In scope: one public loader function, its dedicated module in monai/data, its export from monai.data, a docs entry, and a unit test module.
- Out of scope: training code, transforms, dataset classes, changes to existing monai.data utilities, new dependencies, and datalist writing or conversion. The only conversion is the image-only wrapping of the "test" key.

## Workflows
Run these steps in order. Raise ValueError at the first failed check.
1. Check that data_list_file_path names an existing file before opening it. A missing file must not reach the file-open call.
2. Open the file and parse it as JSON.
3. Check that the top-level object contains data_list_key. A datalist with only a "test" key fails here under the default "training" key unless the caller passes "test".
4. Take the value under data_list_key as the list of entries.
5. If data_list_key equals "test", convert each entry into an item whose only field is "image" holding the entry. This applies regardless of is_segmentation and happens before validation or path resolution.
6. If base_dir is None, use the directory portion of data_list_file_path, not an absolute path.
7. For each item, in order:
   a. The item must be a mapping.
   b. Resolve "image".
   c. Resolve "label" only when is_segmentation is true. When false, leave it exactly as stored, whatever its type.
   d. Leave all other fields unchanged, without path-joining them.
   e. Missing "image" or "label" is not an error. Add no presence check for either field.
8. Resolve a path value:
   - A string: join it with base_dir and normalize the result (collapse "." and redundant separators). An absolute string stays absolute.
   - A list: every element must be a string. Resolve each element independently as a single string. Elements are never joined to each other. The result keeps the length and order of the input.
   - Any other type is an error.
9. Return the processed items in original order.

## Data model
- Input: a JSON object. Entries live under data_list_key. Other top-level fields (name, labels, modality, counts) are ignored.
- Entries under a non-"test" key are objects. "image" is a string or a list of strings. "label" is a string or list of strings when is_segmentation is true; when false it may be any JSON value, such as an integer. Extra fields are preserved verbatim.
- Entries under "test" are plain path strings, converted to image-only items (step 5).
- Output: a list of objects with the input field names. "image" and, in segmentation mode, "label" hold resolved paths, as a string or a list of the same length and order. All other fields are unchanged.

## API contracts
- Public function name: load_decathalon_datalist. The spelling "decathalon" is the contract and matches the reference; do not respell it. It must be importable as monai.data.load_decathalon_datalist.
- Parameters, in order:
  - data_list_file_path (string path to the JSON datalist). Required.
  - is_segmentation (boolean), default true.
  - data_list_key (string), default "training".
  - base_dir (optional string), default none, meaning the datalist file's directory.
- Type hints are optional. If present, they must cover all four parameters and the return, with base_dir typed as an optional string. Do not mix annotated and unannotated parameters.
- Return: a list of objects as described in Data model.
- Errors: ValueError for every condition under Validation. Never raise FileNotFoundError for a missing datalist.

## Module architecture
- Place the loader in a dedicated module in monai/data. The reference uses decathalon_dataloader. Helpers stay private to that module.
- Register the public name with an explicit import in monai/data/__init__.py, because the existing wildcard import from utils does not guarantee the name.
- Docs: in docs/source/data.rst, after the existing Utilities automodule entry, add a subsection titled "Decathalon DataLoader" underlined with tildes so it nests under Utilities. It holds one autofunction entry for monai.data.load_decathalon_datalist.
- Layering: the loader is a data-layer helper and must not import from transforms, networks, handlers, engines, or other monai packages.

## Implementation constraints
- Standard library only (os and json). Do not change requirements or setup files.
- Keep file access and JSON parsing inside the loader.
- Do not change existing functions or behavior in monai/data/utils.py.
- Path resolution is one private helper, used only for "image" and, in segmentation mode, "label". It handles the string case; the list case applies it to each element.
- Helpers are private (leading underscore). The only new public name is the loader.

## Naming
- Test module: tests/test_load_decathalon_datalist.py, containing class TestLoadDecathalonDatalist. Use "decathalon" consistently in names, docs, and test identifiers.

## Validation
- Missing datalist file: ValueError naming the file, checked before parsing.
- Missing data_list_key: ValueError naming the key and file.
- Non-mapping item: ValueError.
- "image" values, and "label" values in segmentation mode, must be a string or list of strings, with element types checked inside lists.
- Classification labels (is_segmentation false) are not type-checked and pass through unchanged.
- Do not coerce values to strings. A wrongly typed value is an error. Do not require "label" in any mode.
- Raise ValueError for each condition, never another exception type. Messages are f-strings naming the offending file, key, or value, matching repository style. Do not catch and swallow exceptions inside the loader.

## Documentation
- The public function has a Google-style docstring like those in monai/data/utils.py. Its Args block lists each entry as "name (type): description" (for example "data_list_file_path (str): ..."), even with type hints. Describe the is_segmentation label behavior, the data_list_key default, and the base_dir default.
- Describe the return value in a prose paragraph giving its shape. A short illustrative example is allowed.
- The docs/source/data.rst entry is required (see Module architecture).

## Compatibility
- Additive only. Existing monai.data names, signatures, and behaviors are unchanged.
- Must run on the repository's target Python version (3.9 in the recorded environment).

## Maintainability
- Every new or changed Python file (loader module, monai/data/__init__.py export line, test module) must be black-formatted at line length 120, because runtests.sh runs black --check and flake8 and pyproject.toml and setup.cfg set the limit to 120. This is a gate.
- Lines that fit in 120 columns stay on one line. A bracketed list, dict, or call that does not fit is split one element per line with a trailing comma.
- The limit applies to every physical line, including test datalist literals and docstring lines. Black may not be installed, so verify by measurement and by reading the wrapped lines.

## Behavioral acceptance criteria
- Segmentation, training key, base_dir supplied: image and label resolve to normalized paths under base_dir in list order; extra fields are kept.
- List-valued path fields: a list of N relative strings resolves to N normalized paths in input order. A two-element list never becomes one element or one combined path.
- Classification (is_segmentation false), training key, integer label: image resolves; label stays the same integer.
- base_dir omitted: relative values resolve against the datalist's directory. Absolute values stay absolute.
- Key "test" passed explicitly, default is_segmentation, plain string entries: returns one image-only item per entry, first item's image resolved.
- The default "training" key on a datalist with only a "test" key is a missing-key ValueError. This is expected, not a defect to work around.
- A string in a non-path field (for example a class-name string under a non-image, non-label key) is not path-joined.
- A missing file, missing key, non-mapping item, or wrongly typed path value each raises ValueError.

## Test requirements
- The test module imports the public name from monai.data and contains class TestLoadDecathalonDatalist with four tests.
- Every call passes the datalist key and base_dir explicitly, so the key matches a key in that test's datalist.
  - test_seg_values: segmentation, training key, base_dir supplied; image and label resolved using scalar string paths, as the reference does. Any list expectation needs one resolved path per input element, built with the loader's join-and-normalize approach. Never assert a one-element list for a multi-element input.
  - test_cls_values: classification; integer labels stay integers; images resolved.
  - test_seg_no_basedir: base_dir none, training key; absolute image and label paths preserved. Build absolute inputs by joining the temporary directory with each file name. Do not use separators, drive-less roots, or hardcoded leading slashes, since CI runs on Windows, Linux, and macOS.
  - test_seg_no_labels: datalist has only a "test" key with plain string entries. Pass "test" explicitly. Segmentation at default, base_dir supplied, first item's image resolved.
- Build expectations with the loader's path-joining approach so they compare equal on every platform.
- Each test creates its temporary directory and removes it in all outcomes.
- Do not assert the old bare-string return for the "test" key, and do not assert a ValueError for label-less items.
- Include the MONAI license header, use unittest, and end with the standard main guard. The file must be black-clean at line length 120, splitting multi-element lists one element per line and wrapping any datalist literal longer than 120 columns.
