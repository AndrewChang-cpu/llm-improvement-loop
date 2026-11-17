## Goals
- Provide grid-sampled patch iteration over an image dataset. Patch geometry comes from a separate patch generator, each patch can receive a per-patch transform, and each patch can be delivered with its location in the source image (issue 1500).
- Keep patch generation (`PatchIter`) separate from dataset iteration (`GridPatchDataset`), so another patch generator can be supplied without changing the dataset class.
- Keep all grid geometry in the existing `iter_patch` utility, the single source of patch coordinates.

## Scope
- In scope: `monai/data/grid_dataset.py` (new `PatchIter`, reworked `GridPatchDataset`, docstring example fix in `PatchDataset`), `monai/data/utils.py` (`iter_patch` output and docstring), `monai/data/__init__.py` (export of `PatchIter`), `docs/source/data.rst` (autodoc entry), and a new `tests/test_grid_dataset.py`.
- Out of scope: behavior of `PatchDataset`, `iter_patch_slices`, `get_valid_patch_size`, and `apply_transform`. The only utility change outside `iter_patch` is the `set_rnd` fix under Reliability.

## Assumptions
- Each image item is an array-like whose first dimension is the channel dimension. The channel dimension is always yielded whole, and patch sizes exclude it.
- The image dataset supports `len()`. Iterable-only image datasets are not supported.
- The patch transform is a MONAI transform that accepts a single patch array.
- A patch generator accepts one image item at a time. With a custom generator, `GridPatchDataset` does not inspect the item type.

## Terminology
- Image item: one element returned by indexing the image dataset.
- Patch: a sub-region of one image item with the full channel extent and the requested spatial size, taken from a padded copy so border patches are valid.
- Patch generator: a callable that takes one image item and returns an iterable of tuples. The first element of each tuple is the patch. The second element, if present, is the coordinate array. Further elements are ignored. `PatchIter` is the built-in patch generator.
- Coordinates: an integer array with one row per dimension of the image item, including the channel dimension. Each row holds the start and stop of that dimension for the patch, in the original unpadded image frame.
- Grid sampling: patches step by the patch size from the start position. The first spatial dimension varies fastest.

## Workflows
Patch generation (`PatchIter`, once per image item):
- Build the spatial patch size with a "whole dimension" entry prepended for the channel dimension.
- Delegate to `iter_patch` with copy-back disabled, the start position unchanged (no channel entry added or removed), and the padding mode and options unchanged.
- Yield each tuple from `iter_patch` unchanged.

Dataset iteration (`GridPatchDataset`):
- Index range: 0 to the length of the image dataset. Inside a data-loader worker, split the range evenly: per_worker is the ceiling of length divided by the number of workers, and this worker takes indices from worker_id times per_worker up to the smaller of that start plus per_worker and the length. Outside a worker, use the full range.
- For each index, fetch the image item and iterate the patch generator over it.
- If `with_coordinates` is false, apply the transform to the patch alone (when set) and yield only the patch.
- If `with_coordinates` is true, apply the transform to the patch alone (when set) and yield the pair (transformed patch, coordinates).
- The transform never receives the tuple or the coordinates.

## Data model
- Image item: a channel-first array.
- Patch: a spatial sub-array with the whole channel dimension. It is a view into a padded copy, so in-place changes do not reach the image (copy-back is disabled).
- Coordinates: an integer array of shape (number of dimensions including channel, 2). Row i is [start_i, stop_i] in the original frame. The channel row is [0, C]. Stop can exceed the image extent for border patches. Start is negative only when the start position is negative.
- Dataset element: a patch when `with_coordinates` is false, or a (patch, coordinates) pair when true. Coordinates must be a numeric array, not a tuple of slice objects, so default data-loader collation can batch them.

## API contracts
`PatchIter` (public, exported from `monai.data`):
- Construction options: `patch_size` (sequence of ints; 0 or None selects the whole dimension; the channel is excluded, and its whole-channel entry is added internally). `start_pos` (sequence giving a position in the full channel-first array, so its first entry refers to the channel dimension; default empty, meaning 0 in every dimension). It is normalized to a tuple on construction, and that tuple is passed to `iter_patch` unchanged. `mode` (default wrap; accepts a NumpyPadMode member or its string value). Keyword padding options are forwarded to NumPy padding. Construction does no image work.
- Invocation: takes one image item and returns an iterable of (patch, coordinates) tuples, as produced by `iter_patch`.

`GridPatchDataset` (public, subclass of the torch IterableDataset):
- Constructor parameters, in order: `dataset` (the image dataset), `patch_iter` (required patch generator, no default), `transform` (optional, default none), `with_coordinates` (boolean, default true).
- It must not accept `patch_size`, `start_pos`, `mode`, or padding options. Those belong to `PatchIter`.
- Iteration behavior is defined in Workflows.

`iter_patch` (existing public utility, same name):
- Input parameters are unchanged: array, patch size, start position, copy-back flag, mode, and padding options.
- Each yielded item becomes a pair of the patch view and its coordinate array, as described in Data model. Previously each item was the patch alone.
- It is the only place that knows the padding offsets used to compute coordinates.

Package exports: `monai.data` exports `PatchIter` alongside `GridPatchDataset` and `PatchDataset`. The `__all__` list of the grid dataset module includes `PatchIter`.

## Module architecture
- `monai/data/grid_dataset.py`: `PatchIter` owns patch generation options and delegates geometry. `GridPatchDataset` owns iteration, worker partitioning, per-patch transforms, and the coordinate toggle. `PatchDataset` keeps its behavior.
- `monai/data/utils.py`: `iter_patch` owns padding, slicing (through the existing `iter_patch_slices`), and coordinate computation.
- `monai/data/__init__.py`: re-exports `PatchIter` from the grid dataset module.
- `docs/source/data.rst`: an autodoc section for `PatchIter` placed directly after the `GridPatchDataset` section within the patch-based dataset group.
- Layering: patch generation sits below dataset iteration. The dataset consumes a generator and performs no padding or slice arithmetic.

## Implementation constraints
- `GridPatchDataset` takes the patch generator as an injected callable and must not hard-code `iter_patch`.
- Do not reimplement padding, slicing, grid stepping, or coordinate offsets in the grid dataset module, do not build a parallel grid path, and do not depend on `iter_patch` internal padded offsets.
- Normalize `start_pos` in `PatchIter` with the existing `ensure_tuple` helper from the utilities package, not with hand-written type checks or `tuple(...)` conversion. `ensure_tuple` keeps a string and a zero-dimensional tensor as single values, which `tuple(...)` does not.
- Apply the transform through the existing `apply_transform` helper with its map-items behavior disabled, so the transform receives one patch.
- Each image item is a single image. Do not iterate over channels or zip multiple arrays in lockstep. The old multi-array behavior is removed.
- Asymmetry: the channel entry is prepended to `patch_size` only. `PatchIter` never gives `start_pos` a channel entry; a caller's `start_pos` is interpreted against the full array, exactly as `iter_patch` interprets it.
- Keep the padding-options parameter annotated as a `Dict` mapping, as the original constructor and the reference do.
- Do not add new public names for coordinate helpers to the utility module.

## Dependencies
- `grid_dataset` depends on: torch (IterableDataset and worker info), NumPy (ceiling for the worker split, replacing `math`), the base dataset class, `iter_patch` from the utility module, `apply_transform` from the transforms package, and `NumpyPadMode` and `ensure_tuple` from the utilities package.
- The utility module must not import the grid dataset module. The grid dataset module depends on the utility module, never the reverse.
- No new third-party dependencies.

## Naming
- `PatchIter`: CamelCase, public, exported from `monai.data`, and listed in the grid dataset `__all__`.
- Parameter names: `patch_size`, `start_pos`, `mode`, padding options, `dataset`, `patch_iter`, `transform`, `with_coordinates`.
- Test module: `tests/test_grid_dataset.py` with class `TestGridPatchDataset`.

## Validation
- The image dataset must support length; this is checked when iteration starts.
- `iter_patch` validates patch size and start position: 0 or None selects the whole dimension, and sizes larger than the image are clipped. A start position shorter than the array's dimension count is padded with zeros at the end; a longer one is truncated.
- The mode is validated when `PatchIter` converts it to NumpyPadMode during construction.
- Do not add silent fallbacks for generator output arity. A generator yielding only one element while coordinates are requested fails by unpacking.

## Error handling
- An image dataset without length raises NotImplementedError with the exact message text: image dataset must implement `len()`. (The message ends with a period.) Raise it when the length cannot be obtained, and do not change the wording.
- An invalid mode propagates the conversion error from NumpyPadMode.
- Exceptions from the transform propagate through `apply_transform`, which wraps them as RuntimeError. Do not swallow them.
- Do not catch exceptions raised by the patch generator.

## Documentation
- Every edited Python module and the new test module keeps, or begins with, the repository's 10-line Apache license header verbatim, including "Copyright 2020 - 2021 MONAI Consortium" and the standard Apache 2.0 notice. Editing must not alter these lines.
- `GridPatchDataset` class docstring: explain grid sampling through a patch generator plus a per-patch transform. Include a usage example that builds a list of single-channel images, a `PatchIter` with patch size and start position, a per-patch intensity transform, and a dataset iterated through a two-worker data loader. State the resulting patch shape and coordinate format. The example must match actual outputs.
- `GridPatchDataset` constructor docstring: document `dataset`, `patch_iter` (must yield tuples whose first element is the patch and second is the coordinates; reference `PatchIter`), `transform`, and `with_coordinates` (default true).
- `PatchIter` class docstring: a short summary only. Argument descriptions (patch size, start position, mode, padding options) go in the constructor docstring's Args section, following the `GridPatchDataset` constructor layout. A Note there states that the channel dimension is excluded from patch size, with a worked example for a one-channel 3D image. Start position is described as a position in the full channel-first array, channel entry included, matching `iter_patch`.
- `iter_patch` docstring: the Yields section describes each item as a patch view paired with its coordinate array. Its Note gives the coordinate format as start and stop per dimension, including the channel dimension.
- Docstring examples must state dimensionality correctly, counting the channel dimension. A channel-first array of shape (1, 4, 4) is a one-channel 2D image with three dimensions, so its coordinates have three rows.
- Docstring prose and code lines stay within 120 characters, including indentation.
- `PatchDataset` docstring example: replace the deprecated NumPy float alias with the builtin float.
- `docs/source/data.rst`: add a `PatchIter` autodoc entry with members, in the same heading style as surrounding entries, directly after `GridPatchDataset`.

## Reliability
- Worker partitioning assigns each index to exactly one worker, with no index skipped or repeated.
- The `set_rnd` seeding helper, when recursing into object attributes, skips attribute names starting with a double underscore.
- Patches are views of a padded copy. Because copy-back is disabled, in-place changes to a patch do not change the source image.

## Maintainability
- Lines are at most 120 characters in every edited module, including the test module.
- Format new and edited Python code as the repository's black configuration would at line length 120. A call or literal that fits within 120 columns is one line unless it ends with a trailing comma. A split call must exceed 120 columns when joined or end with a trailing comma. Do not hand-wrap short calls.
- Every import in each edited module must be used. Remove imports that only replaced code used, including `math` once NumPy provides the ceiling. No duplicate imports.
- Grid geometry exists in one place only: the utility module.
- Edits are limited to the regions the feature needs. Unrelated lines, including license headers and existing imports, are preserved verbatim unless the feature requires changing them.

## Compatibility
- Intentional breaking change: the old `GridPatchDataset` constructor form (`patch_size`, `start_pos`, `mode`, padding options) is removed. Callers move to `PatchIter`. Do not add a shim that accepts the old form.
- Behavior change: each dataset item is a single image, not a sequence of arrays.
- Behavior change: coordinates are yielded by default.
- Behavior change: `iter_patch` callers receive (patch, coordinates) pairs.
- Additive: the `PatchIter` export. `PatchDataset` is unaffected.

## Operations
- Environment: Python 3.9 with the repository installed in editable mode and pytest available.
- Verification: run pytest on `tests/test_grid_dataset.py`. Pull-request checklist items about local quick-test runs are not requirements.

## Behavioral acceptance criteria
1. With a custom generator that yields (item, index) tuples over string items and `with_coordinates` false, a data loader with batch size 3 yields the expected contiguous chunks. The union of the chunks has the same total length as the input.
2. Two single-channel 4x4 images, `PatchIter` with patch size 2x2 and start position (0, 0), and a per-patch RandShiftIntensity with offset 1.0 and probability 1.0 under seed 1234: a data loader with batch size 2 yields patch batches of shape (2, 1, 2, 2).
3. For each 4x4 image, the four patches in visit order have coordinate arrays of shape (3, 2). The channel row is [0, 1]. The spatial rows, as (dimension 1 range, dimension 2 range), are in order: (0-2, 0-2), (2-4, 0-2), (0-2, 2-4), (2-4, 2-4).
4. With the default `with_coordinates`, iteration yields (patch, coordinates) pairs, and the data loader batches the coordinates without error.
5. The transform receives a single patch array of shape (channel, height, width), never a tuple. With no transform, patches pass through unchanged.
6. On non-Windows platforms, a two-worker data loader over the same dataset yields the same number of batches, and its final batch has the same coordinates as the single-process final batch. Its patch values are not expected to equal single-process values; they must match the two-worker pinned values in Test requirements.
7. An image dataset without length raises NotImplementedError with the exact message in Error handling.
8. `PatchIter` is importable from `monai.data`.
9. For a channel-first array with more than two dimensions, the `PatchIter` start position applies to the full array including the channel entry. A start position of (0, 4, 4, 4) on a one-channel 20x20x20 image yields the same patch grid as passing that start position to `iter_patch` directly.

## Test requirements
- Create `tests/test_grid_dataset.py` with class `TestGridPatchDataset` containing `test_shape` and `test_loading_array`. These are the FAIL_TO_PASS tests.
- The custom generator used by `test_shape` is a function defined at module scope. It must not be nested, local, or a lambda. Reason: the two-worker DataLoader pickles the dataset and generator for worker processes, and under the spawn start method (the default on macOS) local functions cannot be pickled.
- `setUp` sets determinism with seed 1234. `tearDown` resets determinism to none.
- `test_shape`: string items with the module-level generator that yields one (character, index) tuple per character of each string item, `with_coordinates` false, batch size 3. Use 0 workers on Windows and 2 workers elsewhere. Compare sorted output and total length.
- `test_loading_array`: two 1x4x4 float images, `PatchIter` 2x2 with start position (0, 0), and RandShiftIntensity with offset 1.0 and probability 1.0. Call `set_determinism` with seed 1234 once, at the start of the test, before constructing the transform, generator, dataset, or any loader. Do not call it again anywhere in the test.
- Single-process block (num_workers 0): check every batch's shape as (2, 1, 2, 2). For the final batch, check patch values and coordinate arrays. Expected final-batch patch values: first patch rows (1.7413, 2.7413) and (5.7413, 6.7413); second patch rows (9.1419, 10.1419) and (13.1419, 14.1419). Expected final-batch coordinates: first patch channel [0, 1], dimension 1 [0, 2], dimension 2 [2, 4]; second patch channel [0, 1], dimension 1 [2, 4], dimension 2 [2, 4].
- Single-process patch values use a relative tolerance of 1e-5 with no absolute tolerance (the expected value scaled by 1e-5, not an absolute bound of 1e-5). Coordinates are compared with the same relative tolerance, or exactly, since they are integers.
- Two-worker block (non-Windows platforms only): runs immediately after the single-process block in the same test, reusing the same dataset, transform, and generator objects created at the start of the test. Do not call `set_determinism`, `set_random_state`, or any seeding helper, and do not rebuild those objects, between the blocks. Reason: a zero-worker DataLoader construction draws a seed from the global random state and reseeds dataset components, so extra seeding or rebuilding changes the draws the two-worker pinned values depend on.
- In the two-worker block, check every batch's shape as (2, 1, 2, 2). For the final batch, check coordinates against the same values as the single-process block, and check patch values with a relative tolerance of 1e-3 against their own pinned values: first patch rows (2.3944, 3.3944) and (6.3944, 7.3944); second patch rows (10.6551, 11.6551) and (14.6551, 15.6551). Do not compare two-worker patch values with single-process values.
- Every expected value in `test_loading_array` must be a concrete numeric literal from the constants above. Placeholders (empty, None, NaN, or values to be filled later) are not allowed.
- Do not compute expected values with a second transform instance seeded by hand, and do not call `set_random_state` on the transform between constructing the single-process DataLoader and iterating it.
- Assertions on the missing-length error message must use a literal substring check on the exception text, not regex-based assertions such as assertRaisesRegex, because the message contains regex metacharacters.
- Test module code follows the Maintainability formatting and import rules.
- Do not place grid-dataset tests in `tests/test_patch_dataset.py`.
