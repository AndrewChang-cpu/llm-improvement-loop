# Decathalon datalist loader

## Goals
- Provide a public loader that reads a Medical Segmentation Decathlon style datalist JSON file and returns per-case items whose image and label paths are resolved against a base directory, for segmentation or classification.
- The feature is additive and not a breaking change.

## Scope
- In scope: one public loader function, a dedicated loader module in monai/data, its explicit export from the monai.data package, a docs entry, and a unit test module.
- Out of scope: training code, transforms, dataset classes, changes to existing monai.data utilities, new third-party dependencies, and datalist writing or conversion tools. The only conversion is the image-only wrapping of the "test" key (see Workflows).

## Workflows
Run the following steps in order. Raise ValueError at the first failed check.
1. Check that data_list_file_path names an existing file before opening it. A missing file must not reach the open call.
2. Open the file and parse it as JSON.
3. Check that the top-level object contains data_list_key. The default key is "training", so a datalist with only a "test" key fails here unless the caller passes "test" explicitly.
4. Take the value under data_list_key as the entry list.
5. If data_list_key equals "test", convert each entry into an item whose only field is "image" holding the entry. This is independent of is_segmentation and happens before validation or path resolution.
6. If base_dir is None, use the directory portion of data_list_file_path (not an absolute-path conversion of it).
7. For each item, in order:
   a. The item must be a mapping.
   b. Resolve the "image" field (step 8).
   c. Resolve the "label" field only when is_segmentation is true. When false, leave the label exactly as stored, whatever its type. An integer class id stays an integer; a class name string stays unchanged.
   d. Leave all other fields unchanged, including string fields. Do not path-join them.
   e. Items lacking "image" or "label" are not errors. Do not add a presence check in either mode.
8. Resolve a path value:
   - A string: join it with base_dir and normalize the result (collapse "." and redundant separators). An absolute string stays absolute through the join.
   - A list: every element must be a string. Each element is a complete path resolved independently, exactly as a single string would be. Elements are never joined to each other or treated as components of one path. The result has the same length and order as the input.
   - Any other type is an error.
9. Return the processed items in original order.

## Data model
- Input: a JSON object. Entries live under data_list_key. Other top-level fields (name, description, labels, modality, counts) are ignored.
- Entries under a non-"test" key are objects. "image" is a string or list of strings. "label" is a string or list of strings when is_segmentation is true; when false it may hold any JSON value, such as an integer. Extra fields are preserved verbatim.
- Entries under "test" are plain path strings in the Decathalon layout, converted to image-only items per Workflows step 5.
- Output: a list of objects with the same field names as their inputs. "image", and "label" in segmentation mode, hold resolved paths: a string when the input was a string, or a list of resolved strings with the same count and order when the input was a list. All other fields are unchanged.

## API contracts
- Public function name: load_decathalon_datalist. The spelling "decathalon" is the contract; do not respell it as "decathlon". It must be importable as monai.data.load_decathalon_datalist.
- Parameters, in order:
  - data_list_file_path: string path to the JSON datalist. Required.
  - is_segmentation: boolean, default true.
  - data_list_key: string, default "training".
  - base_dir: optional string, default none. None means the datalist file's directory.
- Type hints are optional. If present, they must cover all four parameters and the return, and base_dir must be an optional string type, not a bare string with a None default. Do not mix annotated and unannotated parameters.
- Return: a list as described in Data model.
- Errors: ValueError for every condition in Error handling. Never raise FileNotFoundError for a missing datalist.

## Module architecture
- Place the loader in a dedicated module inside monai/data. The reference uses decathalon_dataloader. Helpers stay private to that module.
- Register the public name with an explicit import in monai/data/__init__.py. The existing wildcard import from utils does not guarantee the name.
- Docs: in docs/source/data.rst, add a subsection titled "Decathalon DataLoader" after the existing Utilities automodule entry, underlined with tildes so it nests under Utilities. It holds one autofunction entry for monai.data.load_decathalon_datalist, required because the Utilities automodule does not cover the new module.
- Layering: data-layer helper. It must not import from transforms, networks, handlers, engines, or other monai packages.

## Implementation constraints
- Standard library only. Do not change requirements or setup files.
- File access and JSON parsing stay inside the loader.
- Do not change existing functions or behavior in monai/data/utils.py.
- One private path-resolution helper handles the string and list cases, applying the string case to each list element. It is used only for "image" and, in segmentation mode, "label". Other fields never reach it.
- Helpers are private (leading underscore). The only new public name is the loader.

## Dependencies
- Standard library only: os and json, as the reference uses.
- The loader imports no monai modules. The only package-level change is the explicit export in monai/data/__init__.py.

## Naming
- Public name: load_decathalon_datalist.
- Private helpers: leading underscore.
- Test module: tests/test_load_decathalon_datalist.py, containing class TestLoadDecathalonDatalist. Use "decathalon" consistently in names, docs, and test identifiers.

## Validation
- The datalist file must exist before parsing.
- data_list_key must be present in the parsed JSON.
- Every item must be a mapping.
- "image" values, and "label" values in segmentation mode, must be a string or a list of strings; check element types inside lists.
- Classification labels are not type-checked and pass through unchanged.
- Do not coerce values to strings. A wrongly typed value is an error.
- Do not require "label" in any mode.

## Error handling
- Missing datalist file: ValueError naming the file.
- Missing data_list_key: ValueError naming the key and the file.
- Non-mapping item: ValueError.
- Path value that is neither string nor list, or a list containing a non-string: ValueError.
- Use ValueError with f-string messages naming the offending file, key, or value, matching repository style.
- Do not catch and swallow exceptions inside the loader.

## Documentation
- The public function has a Google-style docstring like monai/data/utils.py. Its Args block lists each entry as "name (type): description" (for example "data_list_file_path (str): ..."), even when the signature has type hints. Describe the is_segmentation label behavior, the data_list_key default, and the base_dir default (datalist directory).
- Describe the return value in a prose paragraph giving its shape. A Returns heading is optional; a Raises section is optional. A short illustrative example is allowed but the prose is required.
- The docs/source/data.rst entry is required (see Module architecture).

## Compatibility
- Additive only. Existing monai.data names, signatures, and behaviors are unchanged.
- Must run on the repository's target Python (3.9 in the recorded environment).

## Maintainability
- Every new or changed Python file (loader module, monai/data/__init__.py export line, test module) must be black-formatted at line length 120, as runtests.sh (black --check, flake8) and pyproject.toml/setup.cfg require. This is a gate.
- A statement that fits in 120 columns stays on one line. Do not hand-wrap a statement black would join.
- A bracketed literal or call that does not fit is split one element per line with a trailing comma. Never put several elements on one continuation line.
- Every physical line in new Python files, including test datalist literals and docstrings, must be at most 120 characters. Measure each line before finishing; wrap any longer line under these rules. Black may not be installed, so verify by reading.

## Behavioral acceptance criteria
- Segmentation, training key, base_dir supplied: image and label resolve to normalized paths under base_dir, in list order, and extra fields are kept.
- List-valued path fields: a list of N relative strings resolves to N normalized paths under base_dir, in input order. A two-element list never becomes one element or one combined path.
- Classification (is_segmentation false), training key, integer label: image resolves; label stays the same integer.
- base_dir omitted: relative values resolve against the datalist file's directory. Absolute values stay absolute.
- Key "test" passed explicitly, is_segmentation default (true), plain string entries without labels: succeeds, returning one image-only item per entry, first item's image resolved.
- Default "training" key on a datalist with only a "test" key: missing-key ValueError. This is expected, not a defect to work around.
- A string in a non-path field (for example a class-name string under a non-image, non-label key) is not path-joined.
- A missing file, missing key, non-mapping item, or wrongly typed path value each raises ValueError.

## Test requirements
- The test module imports the public name from monai.data and contains class TestLoadDecathalonDatalist with four tests.
- Every call passes data_list_key and base_dir explicitly, so the key always matches a key present in that test's datalist.
  - test_seg_values: segmentation, training key, base_dir supplied; image and label resolved. Scalar string paths, as the reference does. If a test uses a list-valued image or label, the expectation is a list with one resolved path per input element, built with the same join-and-normalize approach. Never assert a one-element list for a multi-element input, and never treat list elements as components of one path.
  - test_cls_values: classification, integer labels stay integers, images resolved.
  - test_seg_no_basedir: base_dir none, training key; absolute image and label paths preserved and checked. Build absolute inputs and expectations by joining the temporary directory path with each file name, as other tests do. Never use a path separator, drive-less root, or hardcoded leading slash, because these are not absolute on Windows, which CI also runs.
  - test_seg_no_labels: datalist has only a "test" key with plain string entries. Pass "test" explicitly as data_list_key; do not rely on the default. Segmentation at default, base_dir supplied, first item's image resolved.
- Tests must not assume POSIX path conventions. Build expectations with the loader's join approach so they compare equal on every platform.
- Each test creates its temporary directory and removes it in all outcomes.
- Do not assert the old bare-string return for the "test" key, and do not assert a ValueError for label-less items.
- Include the MONAI license header, use unittest, end with the standard main guard.
- Follow PEP 8 blank lines (two before a top-level class). The file must be black-clean at line length 120, per Maintainability.
