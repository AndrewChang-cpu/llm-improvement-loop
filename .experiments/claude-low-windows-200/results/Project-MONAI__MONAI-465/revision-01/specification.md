# Decathalon datalist loader

## Goals
- Provide a public loader that reads a Medical Segmentation Decathlon style dataset JSON file (datalist) and returns a list of per-case items whose image and label path fields are resolved against a base directory. Users can load Decathlon datasets directly for segmentation or classification.
- Users can also convert their own datalists to the Decathlon layout and load them with the same loader.
- The feature is additive. It is not a breaking change.

## Scope
- In scope: one public loader function, its export from the monai.data package, a docs entry, and a unit test module.
- Out of scope: training code, transforms, dataset classes, changes to the behavior of existing monai.data utilities, and any new third-party dependency.
- PR-template content (status, change-type checkboxes) is not a requirement and must not be carried into the implementation or its docstring.

## Workflows
Implement the loader as the following ordered procedure. Raise ValueError at the first failed check.
1. Check that data_list_file_path names an existing file before opening it. Do not let a missing file reach the file-open call.
2. Open the file and parse it as JSON.
3. Check that the top-level JSON object contains data_list_key. Missing key is an error.
4. Take the value stored under data_list_key as the list of entries.
5. If data_list_key equals "test", convert each entry into an image-only item whose only field is "image" holding the entry. This conversion is independent of is_segmentation. Do it before any validation or path resolution.
6. If base_dir is None, use the directory portion of data_list_file_path (the directory of the datalist, not an absolute-path conversion of it).
7. For each item, in order:
   a. The item must be a mapping. Otherwise it is an error.
   b. For field "image": resolve the value (see step 8).
   c. For field "label": resolve the value only when is_segmentation is true. When is_segmentation is false, leave the label exactly as stored, whatever its type (for example an integer class id stays an integer, and a string class name stays unchanged).
   d. Any other field: leave unchanged. Do not path-join other string fields.
   e. Items that lack "image" or "label" are not errors. Do not add a presence check for either field in either mode.
8. Resolve a path value as follows:
   - A string: join it with base_dir and normalize the result (collapse "." and redundant separators). An absolute string keeps its absolute meaning through the join.
   - A list: every element must be a string, otherwise it is an error. Resolve each element the same way and keep the list order.
   - Any other type: error.
9. Return the processed items in the original order.

## Data model
- Input: a JSON object. The entry list lives under data_list_key. Other top-level fields (for example name, description, labels, modality, counts) are ignored by the loader.
- Entries under a non-"test" key are objects. "image" is a string or a list of strings. "label" is a string or a list of strings when is_segmentation is true. When is_segmentation is false, "label" may hold any JSON value, such as an integer class id. Extra fields are preserved verbatim.
- Entries under the "test" key are plain path strings in the Decathlon layout. The loader converts them to image-only items (see Workflows, step 5).
- Output: a list of objects. Each object has the same field names as its input item. "image" and, in segmentation mode, "label" hold resolved paths (strings, or lists of strings when the input was a list). All other fields are unchanged.

## API contracts
- Public function name: load_decathalon_datalist. The spelling "decathalon" is the contract and matches the reference. Do not respell it to "decathlon" and do not rely on a differently spelled name. The function must be importable as monai.data.load_decathalon_datalist.
- Parameters, in this order:
  - data_list_file_path: string path to the JSON datalist. Required.
  - is_segmentation: boolean, default true.
  - data_list_key: string, default "training".
  - base_dir: string or none, default none. None means the directory of the datalist file.
- Return: a list of objects as described in Data model.
- Errors: ValueError for every condition listed under Error handling. The loader must not raise FileNotFoundError for a missing datalist.

## Module architecture
- Place the loader in a dedicated module inside the monai/data package. The reference uses a module named decathalon_dataloader. Helpers stay private to that module.
- Register the public name with an explicit import in monai/data/__init__.py. Relying only on the existing wildcard import from utils is not sufficient, because it does not guarantee the required name. If the loader is placed in utils instead, the explicit registration is still required.
- Documentation: add a section to docs/source/data.rst after the existing utilities automodule entry, containing an autofunction entry for monai.data.load_decathalon_datalist.
- Layering: the loader is a data-layer helper. It must not import from transforms, networks, handlers, engines, or other monai packages.

## Implementation constraints
- Use only the Python standard library. Do not change requirements or setup files.
- Keep file access and JSON parsing inside the loader.
- Do not change existing functions or their behavior in monai/data/utils.py.
- Path-resolution logic is a single private helper used only for the "image" and "label" fields (and only for "label" in segmentation mode). Other fields never pass through it.
- Helper functions are private (leading underscore). The only new public name is the loader.

## Dependencies
- Standard library only: os and json. This is the set the reference uses.
- The loader imports no monai modules. The only package-level change is the explicit export in monai/data/__init__.py.

## Naming
- Public name: load_decathalon_datalist, spelled exactly as above.
- Private helpers: leading underscore.
- Test module: tests/test_load_decathalon_datalist.py, containing class TestLoadDecathalonDatalist. Use "decathalon" consistently in names, docs, and test identifiers.

## Validation
- The datalist file must exist before parsing.
- data_list_key must be present in the parsed JSON.
- Every item must be a mapping.
- "image" values, and "label" values in segmentation mode, must be a string or a list of strings. Check element types inside lists.
- Classification labels (is_segmentation false) are not type-checked and are passed through unchanged.
- Do not coerce values with a conversion such as str(). A wrongly typed value is an error, not a silently converted path.
- Do not require "label" to be present in any mode.

## Error handling
- Missing datalist file: ValueError whose message names the file.
- Missing data_list_key: ValueError whose message names the key and the file.
- Non-mapping item: ValueError.
- Path value that is neither a string nor a list, or a list containing a non-string: ValueError.
- Use ValueError with f-string messages that name the offending file, key, or value, matching repository style.
- Do not catch and swallow exceptions inside the loader.

## Documentation
- The public function has a Google-style docstring with Args and Returns (and Raises) sections, in the style of monai/data/utils.py. Describe the is_segmentation behavior for labels, the data_list_key default, and the base_dir default (datalist directory).
- Describe the returned shape in prose. Do not embed code in the docstring.
- The docs/source/data.rst entry is required even though the utils automodule would otherwise pick up the names in utils.

## Compatibility
- Additive only. Existing monai.data names, signatures, and behaviors are unchanged.
- Must run on the Python version the repository targets (3.9 in the recorded environment).

## Behavioral acceptance criteria
- Segmentation, training key, base_dir supplied: image and label are resolved to normalized paths under base_dir, in list order, and extra fields are kept.
- Classification (is_segmentation false), training key, integer label: image is resolved and the label stays the same integer value.
- base_dir omitted: relative values resolve against the directory containing the datalist file. Absolute values stay absolute.
- Key "test", is_segmentation at its default (true), entries that are plain strings with no labels: the call succeeds and returns one image-only item per entry, with the first item's image resolved.
- A string value in a non-path field (for example a class-name string under a non-image, non-label key) is not path-joined.
- A missing file, a missing key, a non-mapping item, or a wrongly typed path value each raises ValueError.

## Test requirements
- The test module imports the public name from monai.data and contains class TestLoadDecathalonDatalist with four tests:
  - test_seg_values: segmentation, training key, base_dir supplied, image and label resolved.
  - test_cls_values: classification, integer labels, labels remain integers, images resolved.
  - test_seg_no_basedir: base_dir None, absolute image and label paths and the "test" key entries also checked.
  - test_seg_no_labels: key "test", segmentation default, label-less string entries, first item's image resolved.
- Each test creates its temporary directory and removes it in all outcomes. Do not leak temporary directories.
- Do not assert the old bare-string return for the "test" key, and do not assert a ValueError for label-less items.
- Include the MONAI license header, use unittest, and end with the standard main guard.
- Follow PEP 8 blank-line rules (two blank lines before a top-level class) and the 120-character line limit.
