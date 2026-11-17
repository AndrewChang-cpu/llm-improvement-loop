## Goals
- Provide grid-sampled patch iteration over an image dataset. A separate patch generator supplies patch geometry, each patch can receive a per-patch transform, and each patch can be delivered with its location in the source image (issue 1500).
- Keep patch generation (`PatchIter`) separate from dataset iteration (`GridPatchDataset`), so another generator can be supplied without changing the dataset class.
- Keep all grid geometry in the existing `iter_patch` utility, the single source of patch coordinates.

## Scope
- In scope: `monai/data/grid_dataset.py` (new `PatchIter`, reworked `GridPatchDataset`, float alias fix in the `PatchDataset` docstring example), `monai/data/utils.py` (`iter_patch` output and docstring), `monai/data/__init__.py` (export of `PatchIter`), `docs/source/data.rst` (autodoc entry), and a new `tests/test_grid_dataset.py`.
- Out of scope: behavior of `PatchDataset`, `iter_patch_slices`, `get_valid_patch_size`, and `apply_transform`, except the `set_rnd` fix under Reliability.

## Assumptions
- Each image item is a channel-first array-like. The channel dimension is always yielded whole, and patch sizes exclude it.
- The image dataset supports `len()`. Iterable-only datasets are not supported.
- The patch transform is a MONAI transform that accepts a single patch array. A custom patch generator accepts one image item at a time, and `GridPatchDataset` does not inspect item types.

## Terminology
- Image item: one element returned by indexing the image dataset.
- Patch: a sub-region of one image item with the full channel extent and the requested spatial size, taken from a padded copy so border patches are valid.
- Patch generator: a callable that takes one image item and returns an iterable of tuples. The first element is the patch; the second, if present, is its coordinate array. Further elements are ignored. `PatchIter` is the built-in generator.
- Coordinates: an integer array with one row per dimension, channel included, giving start and stop of that dimension in the original unpadded frame.
- Grid sampling: patches step by the patch size from the start position, with the first spatial dimension varying fastest.

## Workflows
Patch generation (`PatchIter`, once per image item):
- Prepend a whole-dimension entry for the channel to the spatial patch size.
- Delegate to `iter_patch` with copy-back disabled; pass the start position, padding mode, and padding options unchanged. Yield each tuple unchanged.

Dataset iteration (`GridPatchDataset`):
- Index range: 0 to the length of the image dataset. Inside a data-loader worker, split the range: per_worker is the ceiling of length divided by the worker count, and this worker takes indices from worker_id times per_worker up to the smaller of that start plus per_worker and the length. Outside a worker, use the full range.
- For each index, fetch the image item and iterate the patch generator over it.
- Apply the transform to the patch alone, when set. If `with_coordinates` is false, yield only the patch; if true, yield (transformed patch, coordinates). The transform never receives the tuple or the coordinates.

## Data model
- Patch: a spatial sub-array with the whole channel dimension, a view into a padded copy, so in-place changes do not write back to the image.
- Coordinates: an integer array of shape (dimensions including channel, 2). Row i is [start_i, stop_i] in the original frame. The channel row is [0, C]. Stop can exceed the image extent for border patches; start is negative only when the start position is negative.
- Dataset element: a patch when `with_coordinates` is false, or a (patch, coordinates) pair when true. Coordinates must be a numeric array, not a tuple of slice objects, so the default collation can batch them.

## API contracts
`PatchIter` (public, exported from `monai.data`):
- Options: `patch_size` (sequence of ints; 0 or None selects the whole dimension; the channel is excluded and added internally). `start_pos` (sequence giving a position in the full channel-first array, so its first entry refers to the channel; default empty, meaning 0 in every dimension). Normalize it to a tuple on construction and pass it to `iter_patch` unchanged. `mode` (default wrap; accepts a NumpyPadMode member or its string value). Keyword padding options go to NumPy padding. Construction does no image work.
- Invocation: takes one image item and returns an iterable of (patch, coordinates) tuples, as produced by `iter_patch`.

`GridPatchDataset` (public, subclass of the torch IterableDataset):
- Constructor parameters, in order: `dataset`, `patch_iter` (required), `transform` (optional, default none), `with_coordinates` (default true).
- Must not accept `patch_size`, `start_pos`, `mode`, or padding options.

`iter_patch` (existing public utility, same name):
- Input parameters are unchanged: array, patch size, start position, copy-back flag, mode, and padding options.
- Each yielded item becomes a (patch view, coordinate array) pair. It is the only place that knows the padding offsets used for coordinates.

Package exports: `monai.data` exports `PatchIter` alongside `GridPatchDataset` and `PatchDataset`.

## Module architecture
- `monai/data/grid_dataset.py`: `PatchIter` owns generation options and delegates geometry; `GridPatchDataset` owns iteration, worker partitioning, transforms, and the coordinate toggle. `PatchDataset` is unchanged.
- `monai/data/utils.py`: `iter_patch` owns padding, slicing (via `iter_patch_slices`), and coordinate computation.
- `monai/data/__init__.py` re-exports `PatchIter`. `docs/source/data.rst` gets an autodoc section for `PatchIter` directly after `GridPatchDataset`.

## Implementation constraints
- `GridPatchDataset` takes the patch generator as an injected callable and must not hard-code `iter_patch`.
- Do not reimplement padding, slicing, grid stepping, or coordinate offsets in the grid dataset module. Do not build a parallel grid path, depend on `iter_patch` internal padded offsets, or add new public coordinate helpers to the utility module.
- Normalize `start_pos` in `PatchIter` with the existing `ensure_tuple` helper, not a hand-rolled conversion: `ensure_tuple` keeps a string and a zero-dimensional tensor as single values, which a plain tuple conversion does not.
- Apply the transform through the existing `apply_transform` helper with its map-items behavior disabled, so the transform receives one patch.
- Each image item is a single image; do not iterate over channels or zip arrays in lockstep.
- Asymmetry: the channel entry is prepended to `patch_size` only. A caller's `start_pos` is interpreted against the full array, channel entry included, exactly as `iter_patch` interprets it.
- Annotate the padding-options parameter as a `Dict` mapping, as the original constructor and the reference do.
- `grid_dataset` may import torch, NumPy, the base dataset class, `iter_patch`, `apply_transform`, `NumpyPadMode`, and `ensure_tuple`. The utility module must not import the grid dataset module. Add no third-party dependencies.

## Validation
- The image dataset must support length, checked when iteration starts.
- `iter_patch` validates patch size and start position: 0 or None selects the whole dimension, sizes larger than the image are clipped, a short start position is padded with zeros at the end, and a long one is truncated.
- The mode is validated when `PatchIter` converts it to NumpyPadMode during construction.
- Do not add silent fallbacks for generator output arity; a one-element yield with coordinates requested fails by unpacking.

## Error handling
- An image dataset without length raises NotImplementedError with the exact message "image dataset must implement `len()`." (ending with a period). Do not change the wording.
- An invalid mode propagates the conversion error from NumpyPadMode.
- Transform exceptions propagate through `apply_transform`, which wraps them as RuntimeError. Do not swallow them or catch generator exceptions.

## Documentation
- Each edited module and the new test module keeps the 10-line Apache license header verbatim.
- `GridPatchDataset` class docstring: explain grid sampling through a patch generator and a per-patch transform. Include a usage example (single-channel images, `PatchIter` with patch size and start position, a per-patch intensity transform, two-worker loader) stating the patch shape and coordinate format. The example must match actual outputs.
- `GridPatchDataset` constructor docstring: document each parameter. `patch_iter` must yield tuples whose first element is the patch and second is the coordinates; reference `PatchIter`.
- `PatchIter` class docstring: a short summary only. Arguments go in the constructor docstring's Args section, in the same layout as `GridPatchDataset`. A Note states that the channel is excluded from patch size, with a worked example for a one-channel 3D image.
- `iter_patch` docstring: the Yields section describes each item as a patch view paired with its coordinate array. Its Note gives the coordinate format, including the channel.
- Docstring examples must count the channel in dimensionality. A channel-first array of shape (1, 4, 4) is a one-channel 2D image with three dimensions, so its coordinates have three rows.
- Docstring lines stay within 120 characters, including indentation.
- `PatchDataset` docstring example: replace the deprecated NumPy float alias with the builtin float.
- `docs/source/data.rst`: add a `PatchIter` autodoc entry with members, in the same heading style as surrounding entries.

## Reliability
- Worker partitioning assigns each index to exactly one worker, with no index skipped or repeated.
- The `set_rnd` seeding helper, when recursing into object attributes, skips attribute names starting with a double underscore.
- Because copy-back is disabled and patches are views of a padded copy, in-place changes do not alter the source image.

## Maintainability
- Format new and edited Python as black would at line length 120, including the test module.
- Every import in each edited module must be used. Remove imports that only replaced code used, including `math`. No duplicate imports.
- Preserve unrelated lines, including license headers and imports.

## Compatibility
- Intentional breaking change: the old `GridPatchDataset` constructor form (`patch_size`, `start_pos`, `mode`, padding options) is removed. Callers move to `PatchIter`. Do not add a shim.
- Behavior changes: each dataset item is a single image, not a sequence of arrays; coordinates are yielded by default; `iter_patch` callers receive (patch, coordinates) pairs.

## Behavioral acceptance criteria
1. With a custom generator yielding (item, index) tuples over string items and `with_coordinates` false, a batch-size-3 loader yields contiguous chunks whose union has the input's total length.
2. Two single-channel 4x4 images, `PatchIter` with patch size 2x2 and start position (0, 0), and a per-patch RandShiftIntensity under seed 1234: a batch-size-2 loader yields patch batches of shape (2, 1, 2, 2).
3. Each 4x4 image yields four patches in visit order with coordinate arrays of shape (3, 2). The channel row is [0, 1]. The spatial rows, as (dimension 1 range, dimension 2 range), are (0-2, 0-2), (2-4, 0-2), (0-2, 2-4), (2-4, 2-4).
4. The transform receives a single patch array of shape (channel, height, width), never a tuple. With no transform, patches pass through unchanged.
5. On non-Windows platforms, a two-worker loader yields the same number of batches, and its final batch has the same coordinates as the single-process final batch. Patch values are checked only against the two-worker pinned values in Test requirements.
6. For a channel-first array with more than two dimensions, a start position of (0, 4, 4, 4) on a one-channel 20x20x20 image yields the same patch grid as calling `iter_patch` directly.

## Test requirements
- `tests/test_grid_dataset.py`, class `TestGridPatchDataset`, containing `test_shape` and `test_loading_array` (the FAIL_TO_PASS tests).
- The generator used by `test_shape` is a module-scope function, not nested, local, or a lambda, because the two-worker DataLoader pickles the dataset under the spawn start method (the macOS default).
- `setUp` sets determinism with seed 1234. `tearDown` resets determinism to none.
- `test_shape`: string items, the module-level generator yielding one (character, index) tuple per character, `with_coordinates` false, batch size 3. Use 0 workers on Windows and 2 elsewhere. Compare sorted output and total length.
- `test_loading_array`: two 1x4x4 float images, `PatchIter` 2x2 with start position (0, 0), and RandShiftIntensity with offset 1.0 and probability 1.0. Call `set_determinism` with seed 1234 once, at the start of the test, before constructing the transform, generator, dataset, or any loader. Do not call it again.
- Single-process block (0 workers): check every batch shape as (2, 1, 2, 2). For the final batch, check patch values and coordinates. Expected patch values: first patch rows (1.7413, 2.7413) and (5.7413, 6.7413); second patch rows (9.1419, 10.1419) and (13.1419, 14.1419). Expected coordinates: first patch channel [0, 1], dimension 1 [0, 2], dimension 2 [2, 4]; second patch channel [0, 1], dimension 1 [2, 4], dimension 2 [2, 4].
- Single-process patch values use a relative tolerance of 1e-5 with no absolute tolerance. Coordinates are integers, compared exactly. Every expected value must be a concrete numeric literal from these constants.
- Two-worker block (non-Windows only): runs immediately after the single-process block, reusing the same dataset, transform, and generator objects. Do not call any seeding helper or rebuild those objects between blocks, because a zero-worker DataLoader construction draws a seed from the global random state and reseeds the dataset components.
- Two-worker block: check every batch shape as (2, 1, 2, 2). For the final batch, check coordinates against the single-process coordinates, and check patch values with a relative tolerance of 1e-3 against their own pinned values: first patch rows (2.3944, 3.3944) and (6.3944, 7.3944); second patch rows (10.6551, 11.6551) and (14.6551, 15.6551). Do not compare two-worker values with single-process values.
- Do not compute expected values with a hand-seeded second transform, and do not call `set_random_state` on the transform between building the single-process DataLoader and iterating it.
- Missing-length assertions use a literal substring check, not assertRaisesRegex, because the message contains regex metacharacters.
