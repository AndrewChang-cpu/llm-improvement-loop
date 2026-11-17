# Decathalon datalist loader

## Goals
- Provide a public loader that reads a Medical Segmentation Decathlon style datalist JSON file and returns per-case items whose image and label paths are resolved against a base directory, for segmentation or classification.
- The feature is additive and not a breaking change.

## Scope
- In scope: one public loader function, a dedicated loader module in monai/data, its explicit export from monai.data, a docs entry, and a unit test module.
- Out of scope: training code, transforms, dataset classes, changes to existing monai.data utilities, new third-party dependencies, and any datalist writing or conversion tool. The only conversion is the image-only wrapping of the "test" key in Workflows.

## Workflows
Run the following ordered procedure. Raise ValueError at the first failed check.
1. Check that data_list_file_path names an existing file before opening it. A missing file must not reach the file-open call.
2. Open the file and parse it as JSON.
3. Check that the top-level object contains data_list_key. A datalist with only a "test" key fails here under the default "training" key unless the caller passes "test" explicitly.
4. Take the value under data_list_key as the list of entries.
5. If data_list_key equals "test", convert each entry into an item whose only field is "image" holding the entry. This is independent of is_segmentation and happens before validation or path resolution.
6. If base_dir is None, use the directory portion of data_list_file_path (the datalist's directory, not an absolute-path conversion).
7. For each item, in order:
   a. The item must be a mapping.
   b. Resolve field "image".
   c. Resolve field "label" only when is_segmentation is true. When false, leave the label exactly as stored, whatever its type (an integer class id stays an integer, a class-name string stays unchanged).
   d. Leave all other fields unchanged, without path-joining string fields.
   e. Items lacking "image" or "label" are not errors. Do not add a presence check for either field in either mode.
8. Resolve a path value:
   - A string: join it with base_dir and normalize the result (collapse "." and redundant separators). An absolute string stays absolute through the join.
   - A list: every element must be a string. Each element is a complete path resolved independently, exactly as a single string. Elements are never joined to each other or treated as components of one path. The result has the same length and order as the input.
   - Any other type is an error.
9. Return the processed items in the original order.

## Data model
- Input: a JSON object. Entries live under data_list_key. Other top-level fields (name, description, labels, modality, counts) are ignored.
- Entries under a non-"test" key are objects. "image" is a string or a list of strings. "label" is a string or a list of strings when is_segmentation is true; when false it may hold any JSON value, such as an integer class id. Extra fields are preserved verbatim.
- Entries under "test" are plain path strings in the Decathalon layout, converted to image-only items (Workflows step 5).
- Output: a list of objects with the same field names as the input items. "image" and, in segmentation mode, "label" hold resolved paths: a string if the input was a string, or a list of resolved strings with the same length and order if the input was a list. All other fields are unchanged.

## API contracts
- Public function name: load_decathalon_datalist. The spelling "decathalon" is the contract and matches the reference. Do not respell it as "decathlon". It must be importable as monai.data.load_decathalon_datalist.
- Parameters, in order:
  - data_list_file_path (string path to the JSON datalist). Required.
  - is_segmentation (boolean), default true.
  - data_list_key (string), default "training".
  - base_dir (optional string), default none, meaning the datalist file's directory.
- Type hints are optional. If present, they must cover all four parameters and the return, and base_dir must be an optional string type, not a bare string with a None default. Do not mix annotated and unannotated parameters.
- Return: a list of objects as described in Data model.
- Errors: ValueError for every condition under Validation and Error handling. Never raise FileNotFoundError for a missing datalist.

## Module architecture
- Place the loader in a dedicated module in monai/data. The reference uses decathalon_dataloader. Helpers stay private to that module.
- Register the public name with an explicit import in monai/data/__init__.py. The existing wildcard import from utils does not guarantee the name.
- Docs: in docs/source/data.rst, after the existing Utilities automodule entry, add a subsection titled "Decathalon DataLoader" underlined with tildes so it nests under Utilities. It holds one autofunction entry for monai.data.load_decathalon_datalist, because the Utilities automodule does not cover the new module.
- Layering: the loader is a data-layer helper and must not import from transforms, networks, handlers, engines, or other monai packages.

## Implementation constraints
- Standard library only (os and json). Do not change requirements or setup files.
- Keep file access and JSON parsing inside the loader.
- Do not change existing functions or behavior in monai/data/utils.py.
- Path resolution is a single private helper used only for "image" and, in segmentation mode, "label". It handles the string case, and the list case applies the string case to each element.
- Helpers are private (leading underscore). The only new public name is the loader.

## Naming
- Public name: load_decathalon_datalist.
- Test module: tests/test_load_decathalon_datalist.py, containing class TestLoadDecathalonDatalist. Use "decathalon" consistently in names, docs, and test identifiers.

## Validation
- Missing datalist file: ValueError naming the file. Check existence before parsing.
- Missing data_list_key: ValueError naming the key and the file.
- Non-mapping item: ValueError.
- "image" values, and "label" values in segmentation mode, must be a string or a list of strings. Check element types inside lists.
- Classification labels (is_segmentation false) are not type-checked and pass through unchanged.
- Do not coerce values to strings. A wrongly typed value is an error, not a silently converted path.
- Do not require "label" in any mode.

## Error handling
- Raise ValueError (never a different exception type) for each condition above. Messages are f-strings naming the offending file, key, or value, matching repository style.
- Do not catch and swallow exceptions inside the loader.

## Documentation
- The public function has a Google-style docstring like the ones in monai/data/utils.py. Its Args block lists each entry as "name (type): description" (for example "data_list_file_path (str): ..."), even when the signature has type hints. Describe the is_segmentation label behavior, the data_list_key default, and the base_dir default (datalist directory).
- Describe the return value in a prose paragraph giving its shape. A Returns heading is optional, as is a Raises section. A short illustrative example block is allowed, but the prose is required.
- The docs/source/data.rst entry is required (see Module architecture).

## Compatibility
- Additive only. Existing monai.data names, signatures, and behaviors are unchanged.
- Must run on the repository's target Python version (3.9 in the recorded environment).

## Maintainability
- Every new or changed Python file (the loader module, the monai/data/__init__.py export line, and the test module) must be black-formatted at line length 120. runtests.sh runs black --check and flake8, and pyproject.toml and setup.cfg set the maximum line length to 120. This is a gate.
- A statement, call, or literal that fits in 120 columns goes on one line. Do not hand-wrap what black would join.
- A bracketed list, dict, or call that does not fit is split one element per line with a trailing comma. Never place several list elements on one continuation line.
- The 120-column limit applies to every physical line, including test datalist literals and docstring lines. Measure each line in the new loader and test modules, and wrap any longer line by the rules above. Black may not be installed, so verify by measurement and by reading the wrapped lines.

## Behavioral acceptance criteria
- Segmentation, training key, base_dir supplied: image and label resolve to normalized paths under base_dir in list order, and extra fields are kept.
- List-valued path fields: a list of N relative strings resolves to N normalized paths under base_dir, in input order. A two-element list never becomes one element or one combined path.
- Classification (is_segmentation false), training key, integer label: image resolves and the label stays the same integer.
- base_dir omitted: relative values resolve against the datalist's directory. Absolute values stay absolute.
- Key "test" passed explicitly, is_segmentation at its default (true), plain string entries with no labels: succeeds and returns one image-only item per entry, with the first item's image resolved.
- The default "training" key on a datalist with only a "test" key is a missing-key ValueError. This is expected behavior, not a defect to work around.
- A string in a non-path field (for example a class-name string under a non-image, non-label key) is not path-joined.
- A missing file, missing key, non-mapping item, or wrongly typed path value each raises ValueError.

## Test requirements
- The test module imports the public name from monai.data and contains class TestLoadDecathalonDatalist with four tests.
- Every call passes the datalist key and base_dir explicitly, so the key always matches a key present in that test's datalist.
  - test_seg_values: segmentation, training key, base_dir supplied; image and label resolved. Use scalar string paths, as the reference does. Any list-valued expectation must have one resolved path per input element, in order, built with the loader's join-and-normalize approach. Never assert a one-element list for a multi-element input.
  - test_cls_values: classification, integer labels stay integers, images resolved.
  - test_seg_no_basedir: base_dir none, training key; absolute image and label paths preserved. Build absolute inputs and expectations by joining the temporary directory with each file name, as the other tests do. Do not use a path separator, drive-less root, or hardcoded leading slash, because those are not absolute on Windows, and CI runs on Windows, Linux, and macOS.
  - test_seg_no_labels: the datalist has only a "test" key with plain string entries. Pass "test" explicitly as data_list_key; do not rely on the default "training". Segmentation at its default, base_dir supplied, first item's image resolved.
- Do not assume POSIX path conventions. Build expectations with the loader's path-joining approach so they compare equal on every platform.
- Each test creates its temporary directory and removes it in all outcomes.
- Do not assert the old bare-string return for the "test" key, and do not assert a ValueError for label-less items.
- Include the MONAI license header, use unittest, and end with the standard main guard.
- Follow PEP 8 blank-line rules. The file must be black-clean at line length 120 (see Maintainability), splitting multi-element lists one element per line and wrapping any datalist literal longer than 120 columns.
