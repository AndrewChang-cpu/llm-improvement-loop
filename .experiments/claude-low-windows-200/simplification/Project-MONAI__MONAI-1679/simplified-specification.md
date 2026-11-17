## Goals
- Provide grid-sampled patch iteration over an image dataset. A separate patch generator supplies patch geometry, each patch can receive a per-patch transform, and each patch can be delivered with its location in the source image (issue 1500).
- Keep patch generation (`PatchIter`) separate from dataset iteration (`GridPatchDataset`), so another generator can be supplied without changing the dataset class.
- Keep all grid geometry in the existing `iter_patch` utility, the single source of patch coordinates.

## Scope
- In scope: `monai/data/grid_dataset.py` (new `PatchIter`, reworked `GridPatchDataset`, float alias fix in the `PatchDataset` docstring example), `monai/data/utils.py` (`iter_patch` output and docstring), `monai/data/__init__.py` (export of `PatchIter`), `docs/source/data.rst` (autodoc entry), and a new `tests/test_grid_dataset.py`.
- Out of scope: behavior of `PatchDataset`, `iter_patch_slices`, `get_valid_patch_size`, and `apply_transform`, apart from the `set_rnd` fix under Reliability.

## Assumptions
- Each image item is a channel-first array-like. The channel dimension is always yielded whole, and patch sizes exclude it.
- The image dataset supports `len()`. Iterable-only datasets are not supported.
- The patch transform is a MONAI transform that accepts a single patch array.
- A custom patch generator accepts one image item at a time. `GridPatchDataset` does not inspect item types.

## Terminology
- Image item: one element returned by indexing the image dataset.
- Patch: a sub-region of one image item with the full channel extent and the requested spatial size, taken from a padded copy so border patches are valid.
- Patch generator: a callable that takes one image item and returns an iterable of tuples. The first element is the patch; the second, if present, is its coordinate array. Further elements are ignored. `PatchIter` is the built-in generator.
- Coordinates: an integer array with one row per dimension, channel included, giving the start and stop of that dimension in the original unpadded frame.
- Grid sampling: patches step by the patch size from the start position. The first spatial dimension varies fastest.

## Workflows
Patch generation (`PatchIter`, once per image item):
- Prepend a "whole dimension" entry for the channel to the spatial patch size.
- Delegate to `iter_patch` with copy-back disabled, the start position unchanged, and the padding mode and options unchanged. Yield each tuple unchanged.

Dataset iteration (`GridPatchDataset`):
- Index range: 0 to the length of the image dataset. Inside a data-loader worker, split the range across workers: per_worker is the ceiling of length divided by the worker count, and this worker takes indices from worker_id times per_worker up to the smaller of that start plus per_worker and the length. Outside a worker, use the full range.
- For each index, fetch the image item and iterate the patch generator over it.
- Apply the transform to the patch alone (when set). If `with_coordinates` is false, yield only the patch; if true, yield (transformed patch, coordinates). The transform never receives the tuple or the coordinates.

## Data model
- Image item: a channel-first array.
- Patch: a spatial sub-array with the whole channel dimension, a view into a padded copy, so in-place changes do not write back to the image.
- Coordinates: an integer array of shape (dimensions including channel, 2). Row i is [start_i, stop_i] in the original frame. The channel row is [0, C]. Stop can exceed the image extent for border patches; start is negative only when the start position is negative.
- Dataset element: a patch when `with_coordinates` is false, or a (patch, coordinates) pair when true. Coordinates must be a numeric array, not a tuple of slice objects, so the default collation can batch them.

## API contracts
`PatchIter` (public, exported from `monai.data`):
- Options: `patch_size` (sequence of ints; 0 or None selects the whole dimension; the channel is excluded and its whole-channel entry is added internally). `start_pos` (sequence giving a position in the full channel-first array, so its first entry refers to the channel; default empty, meaning 0 in every dimension). It is normalized to a tuple on construction and passed to `iter_patch` unchanged. `mode` (default wrap; accepts a NumpyPadMode member or its string value). Keyword padding options are forwarded to NumPy padding. Construction does no image work.
- Invocation: takes one image item and returns an iterable of (patch, coordinates) tuples, as produced by `iter_patch`.

`GridPatchDataset` (public, subclass of the torch IterableDataset):
- Constructor parameters, in order: `dataset`, `patch_iter` (required), `transform` (optional, default none), `with_coordinates` (default true).
- Must not accept `patch_size`, `start_pos`, `mode`, or padding options.

`iter_patch` (existing public utility, same name):
- Input parameters are unchanged: array, patch size, start position, copy-back flag, mode, and padding options.
- Each yielded item becomes a (patch view, coordinate array) pair instead of the patch alone.
- It is the only place that knows the padding offsets used for coordinates.

Package exports: `monai.data` exports `PatchIter` alongside `GridPatchDataset` and `PatchDataset`.

## Module architecture
- `monai/data/grid_dataset.py`: `PatchIter` owns generation options and delegates geometry. `GridPatchDataset` owns iteration, worker partitioning, per-patch transforms, and the coordinate toggle. `PatchDataset` keeps its behavior.
- `monai/data/utils.py`: `iter_patch` owns padding, slicing (through the existing `iter_patch_slices`), and coordinate computation.
- `monai/data/__init__.py`: re-exports `PatchIter`. `docs/source/data.rst`: an autodoc section for `PatchIter` directly after `GridPatchDataset`.

## Implementation constraints
- `GridPatchDataset` takes the patch generator as an injected callable and must not hard-code `iter_patch`.
- Do not reimplement padding, slicing, grid stepping, or coordinate offsets in the grid dataset module. Do not build a parallel grid path or depend on `iter_patch` internal padded offsets.
- Normalize `start_pos` in `PatchIter` with the existing `ensure_tuple` helper from the utilities package. Do not hand-roll it, because `ensure_tuple` keeps a string and a zero-dimensional tensor as single values, which a plain tuple conversion does not.
- Apply the transform through the existing `apply_transform` helper with its map-items behavior disabled, so the transform receives one patch.
- Each image item is a single image. Do not iterate over channels or zip multiple arrays in lockstep.
- Asymmetry: the channel entry is prepended to `patch_size` only. `start_pos` never receives a channel entry from `PatchIter`; a caller's `start_pos` is interpreted against the full array, exactly as `iter_patch` interprets it.
- Annotate the padding-options parameter as a `Dict` mapping, as the original constructor and the reference do.
- Do not add new public names for coordinate helpers to the utility module.

## Dependencies
- `grid_dataset` depends on: torch (IterableDataset and worker info), NumPy (ceiling for the worker split), the base dataset class, `iter_patch`, `apply_transform`, and `NumpyPadMode` and `ensure_tuple` from the utilities package.
- The utility module must not import the grid dataset module. No new third-party dependencies.

## Validation
- The image dataset must support length, checked when iteration starts.
- `iter_patch` validates patch size and start position: 0 or None selects the whole dimension, sizes larger than the image are clipped, a short start position is padded with zeros at the end, and a long one is truncated.
- The mode is validated when `PatchIter` converts it to NumpyPadMode during construction.
- Do not add silent fallbacks for generator output arity. A generator yielding one element while coordinates are requested fails by unpacking.

## Error handling
- An image dataset without length raises NotImplementedError with the exact message "image dataset must implement `len()`." (ending with a period). Do not change the wording.
- An invalid mode propagates the conversion error from NumpyPadMode.
- Transform exceptions propagate through `apply_transform`, which wraps them as RuntimeError. Do not swallow them, and do not catch exceptions raised by the patch generator.

## Documentation
- Each edited module and the new test module keeps the repository's 10-line Apache license header verbatim.
- `GridPatchDataset` class docstring: explain grid sampling through a patch generator plus a per-patch transform. Include a usage example with a list of single-channel images, a `PatchIter` with patch size and start position, a per-patch intensity transform, and a two-worker data loader. State the resulting patch shape and coordinate format. The example must match actual outputs.
- `GridPatchDataset` constructor docstring: document `dataset`, `patch_iter` (must yield tuples whose first element is the patch and second is the coordinates; reference `PatchIter`), `transform`, and `with_coordinates` (default true).
- `PatchIter` class docstring: a short summary only. Argument descriptions go in the constructor docstring's Args section, in the same layout the `GridPatchDataset` constructor uses. A Note there states that the channel is excluded from patch size, with a worked example for a one-channel 3D image. Start position is described as a position in the full channel-first array, channel entry included.
- `iter_patch` docstring: the Yields section describes each item as a patch view paired with its coordinate array. Its Note gives the coordinate format as start and stop per dimension, including the channel.
- Docstring examples must count the channel in dimensionality. A channel-first array of shape (1, 4, 4) is a one-channel 2D image with three dimensions, so its coordinates have three rows.
- Docstring prose and code lines stay within 120 characters, including indentation.
- `PatchDataset` docstring example: replace the deprecated NumPy float alias with the builtin float.
- `docs/source/data.rst`: add a `PatchIter` autodoc entry with members, in the same heading style as surrounding entries.

## Reliability
- Worker partitioning assigns each index to exactly one worker, with no index skipped or repeated.
- The `set_rnd` seeding helper, when recursing into object attributes, skips attribute names starting with a double underscore.
- Because copy-back is disabled and patches are views of a padded copy, in-place changes do not alter the source image.

## Maintainability
- Lines are at most 120 characters in every edited module, including the test module.
- Format new and edited Python as the repository's black configuration would at line length 120. Split a call across lines only when it exceeds 120 columns when joined or ends with a trailing comma.
- Every import in each edited module must be used. Remove imports that only replaced code used, including `math`. No duplicate imports.
- Edits are limited to the regions the feature needs. Unrelated lines, including license headers and existing imports, are preserved verbatim.

## Compatibility
- Intentional breaking change: the old `GridPatchDataset` constructor form (`patch_size`, `start_pos`, `mode`, padding options) is removed. Callers move to `PatchIter`. Do not add a shim accepting the old form.
- Behavior changes: each dataset item is a single image, not a sequence of arrays; coordinates are yielded by default; `iter_patch` callers receive (patch, coordinates) pairs.
- Additive: the `PatchIter` export. `PatchDataset` is unaffected.

## Operations
- Environment: Python 3.9 with the repository installed in editable mode and pytest available. Verify by running pytest on `tests/test_grid_dataset.py`.

## Behavioral acceptance criteria
1. With a custom generator that yields (item, index) tuples over string items and `with_coordinates` false, a data loader with batch size 3 yields contiguous chunks whose union has the same total length as the input.
2. Two single-channel 4x4 images, `PatchIter` with patch size 2x2 and start position (0, 0), and a per-patch RandShiftIntensity with offset 1.0 and probability 1.0 under seed 1234: a data loader with batch size 2 yields patch batches of shape (2, 1, 2, 2).
3. For each 4x4 image, the four patches in visit order have coordinate arrays of shape (3, 2). The channel row is [0, 1]. The spatial rows, in order, are (0-2, 0-2), (2-4, 0-2), (0-2, 2-4), (2-4, 2-4), listed as (dimension 1 range, dimension 2 range).
4. With the default `with_coordinates`, iteration yields (patch, coordinates) pairs, and the data loader batches the coordinates without error.
5. The transform receives a single patch array of shape (channel, height, width), never a tuple. With no transform, patches pass through unchanged.
6. On non-Windows platforms, a two-worker data loader yields the same number of batches, and its final batch has the same coordinates as the single-process final batch. Patch values are checked only against the two-worker pinned values in Test requirements.
7. An image dataset without length raises NotImplementedError with the exact message in Error handling.
8. `PatchIter` is importable from `monai.data`.
9. For a channel-first array with more than two dimensions, a start position of (0, 4, 4, 4) on a one-channel 20x20x20 image yields the same patch grid as passing it to `iter_patch` directly.

## Test requirements
- `tests/test_grid_dataset.py`, class `TestGridPatchDataset`, containing `test_shape` and `test_loading_array` (the FAIL_TO_PASS tests).
- The custom generator used by `test_shape` is a module-scope function, not nested, local, or a lambda, because the two-worker DataLoader pickles the dataset under the spawn start method (the macOS default).
- `setUp` sets determinism with seed 1234. `tearDown` resets determinism to none.
- `test_shape`: string items, the module-level generator yielding one (character, index) tuple per character of each item, `with_coordinates` false, batch size 3. Use 0 workers on Windows and 2 elsewhere. Compare sorted output and total length.
- `test_loading_array`: two 1x4x4 float images, `PatchIter` 2x2 with start position (0, 0), and RandShiftIntensity with offset 1.0 and probability 1.0. Call `set_determinism` with seed 1234 once, at the start of the test, before constructing the transform, generator, dataset, or any loader. Do not call it again.
- Single-process block (0 workers): check every batch shape as (2, 1, 2, 2). For the final batch, check patch values and coordinates. Expected patch values: first patch rows (1.7413, 2.7413) and (5.7413, 6.7413); second patch rows (9.1419, 10.1419) and (13.1419, 14.1419). Expected coordinates: first patch channel [0, 1], dimension 1 [0, 2], dimension 2 [2, 4]; second patch channel [0, 1], dimension 1 [2, 4], dimension 2 [2, 4].
- Single-process patch values use a relative tolerance of 1e-5 with no absolute tolerance. Coordinates are integers, compared exactly. Every expected value must be a concrete numeric literal from these constants; placeholders are not allowed.
- Two-worker block (non-Windows only): runs immediately after the single-process block in the same test, reusing the same dataset, transform, and generator objects. Do not call any seeding helper or rebuild those objects between the blocks, because a zero-worker DataLoader construction draws a seed from the global random state and reseeds the dataset components.
- Two-worker block: check every batch shape as (2, 1, 2, 2). For the final batch, check coordinates against the single-process coordinates, and check patch values with a relative tolerance of 1e-3 against their own pinned values: first patch rows (2.3944, 3.3944) and (6.3944, 7.3944); second patch rows (10.6551, 11.6551) and (14.6551, 15.6551). Do not compare two-worker values with single-process values.
- Do not compute expected values with a second transform instance seeded by hand, and do not call `set_random_state` on the transform between constructing the single-process DataLoader and iterating it.
- Missing-length error assertions must use a literal substring check on the exception text, not assertRaisesRegex, because the message contains regex metacharacters.
- Test code follows the Maintainability rules. Do not place grid-dataset tests in `tests/test_patch_dataset.py`.
