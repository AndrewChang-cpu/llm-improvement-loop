# Decathalon datalist loader

## Goals
- Provide a public loader that reads a Medical Segmentation Decathlon style datalist JSON file and returns per-case items whose image and label paths are resolved against a base directory, for segmentation or classification.
- The feature is additive and not a breaking change.

## Scope
- In scope: one public loader function, a dedicated loader module in monai/data, its explicit export from the monai.data package, a docs entry, and a unit test module.
- Out of scope: training code, transforms, dataset classes, changes to existing monai.data utilities, new third-party dependencies, and any datalist writing or conversion tool. The only conversion is the image-only wrapping of the "test" key in Workflows.

## Workflows
Run this ordered procedure and raise ValueError at the first failed check.
1. Check that data_list_file_path names an existing file before opening it. A missing file must not reach the file-open call.
2. Open the file and parse it as JSON.
3. Check that the top-level object contains data_list_key. The default key is "training", so a datalist with only a "test" key fails here unless the caller passes "test" explicitly.
4. Take the value under data_list_key as the list of entries.
5. If data_list_key equals "test", convert each entry into an image-only item whose only field is "image" holding the entry. This applies regardless of is_segmentation and happens before any validation or path resolution.
6. If base_dir is None, use the directory portion of data_list_file_path (the datalist's directory, not an absolute-path conversion).
7. For each item, in order:
   a. The item must be a mapping.
   b. Resolve field "image" (step 8).
   c. Resolve field "label" only when is_segmentation is true. When false, leave the label exactly as stored, whatever its type. An integer class id stays an integer and a class-name string stays unchanged.
   d. Leave any other field unchanged. Never path-join other string fields.
   e. Items lacking "image" or "label" are not errors. Do not add a presence check for either field in either mode.
8. Resolve a path value:
   - A string: join it with base_dir and normalize the result (collapse "." and redundant separators). An absolute string stays absolute through the join.
   - A list: every element must be a string. Resolve each element independently, exactly as a single string. Elements are never joined to each other or treated as components of one path. The result has the same length and order as the input.
   - Any other type is an error.
9. Return the processed items in original order.

## Data model
- Input: a JSON object. Entries live under data_list_key. Other top-level fields (name, description, labels, modality, counts) are ignored.
- Entries under a non-"test" key are objects. "image" is a string or list of strings. "label" is a string or list of strings when is_segmentation is true; when false, it may hold any JSON value, such as an integer. Extra fields are preserved verbatim.
- Entries under "test" are plain path strings in the Decathalon layout, converted to image-only items per Workflows step 5.
- Output: a list of objects with the same field names as the input items. "image", and "label" in segmentation mode, hold resolved paths: a string if the input was a string, or a list of resolved strings with the same count and order if the input was a list. All other fields are unchanged.

## API contracts
- Public name: load_decathalon_datalist. The spelling "decathalon" is the contract and matches the reference; do not respell it. It must be importable as monai.data.load_decathalon_datalist.
- Parameters, in order:
  - data_list_file_path (string path to the JSON datalist). Required.
  - is_segmentation (boolean), default true.
  - data_list_key (string), default "training".
  - base_dir (string or none), default none, meaning the datalist file's directory.
- Type hints are optional. If present, they must cover all four parameters and the return. base_dir must be an optional string type, not a bare string with a None default. Do not mix annotated and unannotated parameters.
- Return: the list described in Data model.
- Errors: ValueError for every condition under Error handling. Never raise FileNotFoundError for a missing datalist.

## Module architecture
- Place the loader in a dedicated module in monai/data. The reference uses decathalon_dataloader. Helpers stay private to that module.
- Register the public name with an explicit import in monai/data/__init__.py. The existing wildcard import from utils does not guarantee the name.
- Docs: in docs/source/data.rst, after the existing Utilities automodule entry, add a subsection titled "Decathalon DataLoader" underlined with tildes so it nests under Utilities. It holds one autofunction entry for monai.data.load_decathalon_datalist, because the Utilities automodule does not cover the separate module.
- Layering: the loader is a data-layer helper and imports no transforms, networks, handlers, engines, or other monai packages.

## Implementation constraints
- Use only the standard library. Do not change requirements or setup files.
- Keep file access and JSON parsing inside the loader.
- Do not change existing functions or behavior in monai/data/utils.py.
- Path resolution is a single private helper used only for "image" and, in segmentation mode, "label". It handles the string case, and the list case applies the string case to each element.
- Helpers are private (leading underscore). The only new public name is the loader.

## Dependencies
- Standard library only: os and json, the same set the reference uses.
- The loader imports no monai modules. The only package-level change is the export in monai/data/__init__.py.

## Naming
- Public name: load_decathalon_datalist.
- Private helpers: leading underscore.
- Test module: tests/test_load_decathalon_datalist.py, containing class TestLoadDecathalonDatalist. Use "decathalon" consistently in names, docs, and test identifiers.

## Validation
- The datalist file must exist before parsing.
- data_list_key must be present in the parsed JSON.
- Every item must be a mapping.
- "image" values, and "label" values in segmentation mode, must be a string or list of strings. Check element types inside lists.
- Classification labels (is_segmentation false) are not type-checked and pass through unchanged.
- Do not coerce values to strings. A wrongly typed value is an error, not a silently converted path.
- "label" is never required in any mode.

## Error handling
- Missing datalist file: ValueError naming the file.
- Missing data_list_key: ValueError naming the key and the file.
- Non-mapping item: ValueError.
- Path value neither string nor list, or list with a non-string element: ValueError.
- Use f-string ValueError messages naming the offending file, key, or value, matching repository style.
- Do not catch and swallow exceptions inside the loader.

## Documentation
- The public function has a Google-style docstring like monai/data/utils.py. Its Args block writes each entry as "name (type): description" (for example "data_list_file_path (str): ..."), even when the signature has type hints. Describe the is_segmentation label behavior, the data_list_key default, and the base_dir default (datalist directory).
- Describe the return value in a prose paragraph giving its shape. A Returns heading is optional, and so is a Raises section. A short illustrative example block is allowed; the prose description is required.
- The docs/source/data.rst entry is required.

## Compatibility
- Additive only. Existing monai.data names, signatures, and behaviors are unchanged.
- Must run on the repository's target Python (3.9 in the recorded environment).

## Maintainability
- Every new or changed Python file (loader module, the __init__.py export line, test module) must be black-formatted at line length 120. runtests.sh runs black --check and flake8; pyproject.toml and setup.cfg set the maximum line length to 120. This is a gate.
- A statement, call, or literal that fits in 120 columns goes on one line. Do not hand-wrap what black would join.
- A bracketed list, dict, or call that does not fit is split one element per line with a trailing comma. Never place several elements on one continuation line.
- The 120-column limit applies to every physical line, including test datalist literals and docstring lines. Measure each line in the loader and test modules, and wrap any line over 120, even a data literal.
- Verify by measuring line lengths and checking wrapped lines against these rules, since black may not be installed.

## Behavioral acceptance criteria
- Segmentation, training key, base_dir supplied: image and label resolve to normalized paths under base_dir, in list order, and extra fields are kept.
- List-valued path fields: a list of N relative strings resolves to a list of N normalized paths under base_dir, in order. A two-element list never becomes one element or one combined path.
- Classification, training key, integer label: image resolves and the label stays the same integer.
- base_dir omitted: relative values resolve against the datalist's directory. Absolute values stay absolute.
- Key "test" passed explicitly, segmentation default, plain string entries with no labels: succeeds, returns one image-only item per entry, first item's image resolved.
- Default "training" key on a datalist with only a "test" key is a missing-key ValueError. This is expected, not a defect to work around.
- A string in a non-path field (for example a class-name string under a non-image, non-label key) is not path-joined.
- A missing file, missing key, non-mapping item, or wrongly typed path value each raises ValueError.

## Test requirements
- The test module imports the public name from monai.data and contains class TestLoadDecathalonDatalist with four tests.
- Every call under test passes data_list_key and base_dir explicitly, so the key always matches a key present in that test's datalist.
  - test_seg_values: segmentation, training key, base_dir supplied; image and label resolved. Use scalar string paths for image and label, as the reference does. Any list-valued expectation must have one resolved path per input element, in order, built with the loader's join-and-normalize approach. Never assert a one-element list for a multi-element input.
  - test_cls_values: classification, integer labels stay integers, images resolved.
  - test_seg_no_basedir: base_dir none, training key; absolute image and label paths are preserved and checked. Build absolute values by joining the temporary directory with each file name, as other tests do. Do not build them from a path separator, a drive-less root, or a leading slash, because those are not absolute on Windows, and CI runs on Windows, Linux, and macOS.
  - test_seg_no_labels: datalist has only a "test" key with plain string entries. Pass "test" explicitly as data_list_key and do not rely on the default. Segmentation at its default, base_dir supplied, first item's image resolved.
- Tests must not assume POSIX path conventions. Build expected values with the loader's path-joining approach so they compare equal on every platform.
- Each test creates its temporary directory and removes it in all outcomes.
- Do not assert the old bare-string return for the "test" key, and do not assert a ValueError for label-less items.
- Include the MONAI license header, use unittest, and end with the standard main guard.
- Follow PEP 8 blank-line rules (two blank lines before a top-level class). The file must be black-clean at line length 120, splitting multi-element lists one element per line and wrapping any datalist literal over 120 columns.
