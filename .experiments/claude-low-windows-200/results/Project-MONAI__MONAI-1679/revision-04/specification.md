## Goals
- Provide grid-sampled patch iteration over an image dataset. Patch geometry comes from a separate patch generator, each extracted patch can receive a per-patch transform, and each patch can be delivered together with its location in the source image (issue 1500).
- Keep patch generation (`PatchIter`) separate from dataset iteration (`GridPatchDataset`) so another patch generator can be supplied without changing the dataset class.
- Keep all grid geometry in the existing `iter_patch` utility, which is the single source of patch coordinates.

## Scope
- In scope: `monai/data/grid_dataset.py` (new `PatchIter`, reworked `GridPatchDataset`, docstring example fix in `PatchDataset`), `monai/data/utils.py` (`iter_patch` output and docstring), `monai/data/__init__.py` (export of `PatchIter`), `docs/source/data.rst` (autodoc entry), and a new `tests/test_grid_dataset.py`.
- Out of scope: behavior of `PatchDataset`, `iter_patch_slices`, `get_valid_patch_size`, and `apply_transform`. The only utility change to `set_rnd` is listed under Reliability.

## Assumptions
- Each image item is an array-like whose first dimension is the channel dimension. The channel dimension is always yielded whole, and patch sizes exclude it.
- The image dataset supports `len()`. Iterable-only image datasets are not supported.
- The patch transform is a MONAI transform that accepts a single patch array.
- A patch generator accepts one image item at a time. When a custom generator is supplied, `GridPatchDataset` does not inspect the item type, so items may be any objects the generator accepts.

## Terminology
- Image item: one element returned by indexing the image dataset.
- Patch: a sub-region of one image item with the full channel extent and the requested spatial size. It is taken from a padded copy so border patches are valid.
- Patch generator: a callable that takes one image item and returns an iterable of tuples. The first element of each tuple is the patch. The second element, if present, is the coordinate array for that patch. Any further elements are ignored. `PatchIter` is the built-in patch generator.
- Coordinates: an integer-valued array with one row per dimension of the image item, including the channel dimension. Each row holds the start and stop of that dimension for the patch, in the original unpadded image frame.
- Grid sampling: patches are placed at positions that step by the patch size from the start position. Visit order makes the first spatial dimension vary fastest.

## Workflows
Patch generation (`PatchIter`, once per image item):
- Build the spatial patch size with a "whole dimension" entry prepended for the channel dimension.
- Delegate to the shared `iter_patch` utility with copy-back disabled, the configured start position unchanged (no channel entry added or removed), the padding mode, and the padding options unchanged.
- Yield each tuple from `iter_patch` unchanged.

Dataset iteration (`GridPatchDataset`):
- Index range: start at 0 and end at the length of the image dataset. If a data-loader worker context exists, compute per_worker as the ceiling of length divided by the number of workers. This worker takes indices from worker_id times per_worker up to the smaller of that start plus per_worker and the length. Without a worker context, use the full range.
- For each index, fetch the image item and iterate the patch generator over it.
- If `with_coordinates` is false: take the first element of each tuple as the patch, apply the transform to the patch alone if one is set, and yield only the resulting patch.
- If `with_coordinates` is true: take the patch and the coordinates from each tuple, apply the transform to the patch alone if one is set, and yield the pair (transformed patch, coordinates).
- The transform never receives the tuple or the coordinates.

Pseudocode (informative only, not an implementation):
    for each index in this worker's range:
        item = dataset[index]
        for each output of patch_generator(item):
            patch = output[0]
            if transform is set: patch = transform(patch)
            if with_coordinates: yield (patch, output[1])
            else: yield patch

## Data model
- Image item: a channel-first array.
- Patch: a spatial sub-array with the whole channel dimension. It is a view into a padded copy, so modifying it does not write back to the image (copy-back is disabled).
- Coordinates: an integer-valued array of shape (number of dimensions including channel, 2). Row i is [start_i, stop_i] in the original frame. The channel row is [0, C] for C channels. Stop can exceed the image extent for border patches. Start is negative only when the start position is negative.
- Dataset element: a patch when `with_coordinates` is false, or a (patch, coordinates) pair when it is true. The coordinates must be a numeric array, not a tuple of slice objects, so the default data-loader collation can batch them.

## API contracts
`PatchIter` (public, exported from `monai.data`):
- Construction options: `patch_size` (sequence of ints; 0 or None selects the whole dimension; channel excluded, and the whole-channel entry is added internally). `start_pos` (sequence; a position in the full channel-first array, so it is indexed the same way as the array's dimensions and its first entry refers to the channel dimension; default is empty, meaning 0 in every dimension). It is converted to a tuple on construction (a single scalar becomes a one-element tuple), and that tuple is passed to `iter_patch` unchanged; `iter_patch` pads it with zeros at the end, or truncates it, to the array's number of dimensions. `mode` (default wrap; accepts a NumpyPadMode member or its string value), and keyword padding options forwarded to NumPy padding. Construction does no image work.
- Invocation: takes one image item and returns an iterable of (patch, coordinates) tuples, as produced by `iter_patch`.

`GridPatchDataset` (public, subclass of the torch IterableDataset):
- Constructor parameters, in order: `dataset` (the image dataset), `patch_iter` (required patch generator, no default), `transform` (optional, default none), `with_coordinates` (boolean, default true).
- It must not accept `patch_size`, `start_pos`, `mode`, or padding keyword options. Those belong to `PatchIter`.
- Iteration behavior is defined in Workflows.

`iter_patch` (existing public utility, same name):
- Input parameters are unchanged: array, patch size, start position, copy-back flag, mode, and padding options.
- Output changes: each yielded item is a pair of the patch view and its coordinate array, as described in Data model. Previously each item was the patch alone.
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
- Do not reimplement padding, slicing, grid stepping, or coordinate offsets in the grid dataset module. Do not build a parallel grid path, and do not depend on `iter_patch` internal padded offsets.
- Coordinates must be numeric arrays, not tuples of slice objects.
- Apply the transform through the existing `apply_transform` helper with its map-items behavior disabled, so the transform receives one patch.
- Each image item is a single image. Do not iterate over channels or treat an item as a sequence of arrays zipped in lockstep. The old multi-array behavior is removed.
- Asymmetry between the two size arguments: the channel entry is prepended to `patch_size` only. `start_pos` is never given a channel entry by `PatchIter`; a caller's `start_pos` is interpreted against the full array, exactly as `iter_patch` interprets it.
- Keep the padding-options parameter annotated as a `Dict` mapping, as the original `GridPatchDataset` constructor and the reference do.
- Do not add new public names to the utility module's public list for coordinate helpers.

## Dependencies
- `grid_dataset` depends on: torch (IterableDataset and worker info), NumPy (ceiling for the worker split; replaces the `math` import), the base dataset class, `iter_patch` from the utility module, `apply_transform` from the transforms package, and `NumpyPadMode` and `ensure_tuple` from the utilities package.
- Dependency direction: the utility module must not import the grid dataset module. The grid dataset module depends on the utility module, never the reverse.
- No new third-party dependencies.

## Naming
- `PatchIter`: CamelCase, public, exported from `monai.data`, and listed in the grid dataset `__all__`.
- Parameter names: `patch_size`, `start_pos`, `mode`, padding options, `dataset`, `patch_iter`, `transform`, `with_coordinates`.
- Test module: `tests/test_grid_dataset.py` with class `TestGridPatchDataset`.
- Do not add alternative public helper names for coordinate output to the utility module.

## Validation
- The image dataset must support length; this is checked when iteration starts.
- Patch size and start position are validated by `iter_patch`: 0 or None selects the whole dimension, and sizes larger than the image are clipped. A start position shorter than the array's number of dimensions is padded with zeros at the end; a longer one is truncated.
- The mode is validated when `PatchIter` converts it to NumpyPadMode during construction.
- Do not add silent fallbacks for generator output arity. A generator that yields only one element while coordinates are requested fails by unpacking.

## Error handling
- An image dataset without length raises NotImplementedError with the exact message text: image dataset must implement `len()`. (The message ends with a period.) Raise it when the length cannot be obtained, and do not change the wording.
- An invalid mode propagates the conversion error from NumpyPadMode.
- Exceptions from the transform propagate through `apply_transform`, which wraps them as RuntimeError. Do not swallow them.
- Do not catch exceptions raised by the patch generator.

## Documentation
- Every existing Python module that is edited, and the new test module, keeps or begins with the repository's 10-line Apache license header verbatim above the imports: the line "Copyright 2020 - 2021 MONAI Consortium" followed by the standard Apache 2.0 notice. This covers `monai/data/grid_dataset.py`, `monai/data/utils.py`, `monai/data/__init__.py`, and `tests/test_grid_dataset.py`. Editing a module must not delete or alter these lines.
- `GridPatchDataset` class docstring: explain grid sampling through a patch generator plus a per-patch transform. Include a usage example that builds a list of single-channel images, a `PatchIter` with patch size and start position, a per-patch intensity transform, and a dataset that is iterated through a two-worker data loader. State the resulting patch shape and coordinate format. The example must match actual outputs.
- `GridPatchDataset` constructor docstring: document `dataset`, `patch_iter` (must yield tuples whose first element is the patch and whose second element is the coordinates; reference `PatchIter`), `transform`, and `with_coordinates` (default true).
- `PatchIter` class docstring: a short summary only. Its argument descriptions (patch size, start position, mode, padding options) go in the constructor docstring's Args section, following the layout the `GridPatchDataset` constructor uses. A Note in the constructor docstring states that the channel dimension is excluded from patch size, with a worked example for a one-channel 3D image. The start position is described as a position in the full channel-first array (channel entry included), matching `iter_patch`.
- `iter_patch` docstring: the Yields section describes each yielded item as a patch view paired with its coordinate array. Its Note gives the coordinate format as start and stop per dimension, including the channel dimension.
- `PatchDataset` docstring example: replace the deprecated NumPy float alias with the builtin float.
- `docs/source/data.rst`: add a `PatchIter` autodoc entry with members, in the same heading style as the surrounding entries, directly after `GridPatchDataset`.

## Reliability
- Worker partitioning assigns each index to exactly one worker, with no index skipped or repeated.
- The `set_rnd` seeding helper, when recursing into object attributes, skips attribute names that start with a double underscore.
- Patches are views of a padded copy created by `iter_patch`. Because copy-back is disabled, in-place changes to a patch do not change the source image.

## Maintainability
- Lines are at most 120 characters.
- No duplicate imports and no unused imports. Remove the `math` import once NumPy is used for the ceiling.
- Grid geometry exists in one place only (the utility module).
- Edits to existing files are limited to the regions the feature needs. Unrelated existing lines, including license headers and existing imports, are preserved verbatim unless the feature requires changing them.

## Compatibility
- Intentional breaking change: the old `GridPatchDataset` constructor form (`patch_size`, `start_pos`, `mode`, padding options) is removed. Callers move to `PatchIter`. Do not add a compatibility shim that accepts the old form.
- Behavior change: each dataset item is a single image, not a sequence of arrays.
- Behavior change: coordinates are yielded by default.
- Behavior change: `iter_patch` callers receive (patch, coordinates) pairs.
- Additive: the `PatchIter` export. `PatchDataset` is unaffected.

## Operations
- Environment: Python 3.9 with the repository installed in editable mode and pytest available.
- Verification: run pytest on `tests/test_grid_dataset.py`. The pull-request checklist items about local quick-test runs are not requirements.

## Behavioral acceptance criteria
1. With a custom generator that yields (item, index) tuples over string items and `with_coordinates` false, iterating through a data loader with batch size 3 yields the expected contiguous chunks. The union of the chunks has the same total length as the input.
2. Two single-channel 4x4 images, `PatchIter` with patch size 2x2 and start position (0, 0), and a per-patch RandShiftIntensity with offset 1.0 and probability 1.0 under seed 1234: a data loader with batch size 2 yields patch batches of shape (2, 1, 2, 2).
3. For each 4x4 image, the four patches in visit order have coordinate arrays of shape (3, 2). The channel row is [0, 1]. The spatial rows are, in order: (0-2, 0-2), (2-4, 0-2), (0-2, 2-4), (2-4, 2-4), where the pairs are listed as (dimension 1 range, dimension 2 range).
4. With the default `with_coordinates`, iteration yields (patch, coordinates) pairs, and the data loader batches the coordinates without error.
5. The transform receives a single patch array of shape (channel, height, width), never a tuple. With no transform, patches pass through unchanged.
6. On non-Windows platforms, a two-worker data loader over the same dataset yields the same number of batches, and its final batch has the same coordinates as the single-process final batch. Its patch values are not expected to equal the single-process values, because the random shift is drawn under worker seeding; they must match the two-worker pinned values in Test requirements.
7. An image dataset without length raises NotImplementedError with the exact message text specified in Error handling.
8. `PatchIter` is importable from `monai.data`.
9. For a channel-first array with more than two dimensions, a `PatchIter` start position is applied to the full array including the channel entry: a start position of (0, 4, 4, 4) on a one-channel 20x20x20 image yields the same patch grid as passing that start position to `iter_patch` directly.

## Test requirements
- Create `tests/test_grid_dataset.py` with class `TestGridPatchDataset` containing `test_shape` and `test_loading_array`. These are the FAIL_TO_PASS tests.
- The custom generator used by `test_shape` is a function defined at module scope in the test module. It must not be nested inside a test method, defined as a local function, or written as a lambda. Reason: the two-worker DataLoader sends the dataset, including the generator, to worker processes, and under the spawn start method (the default on macOS) local functions cannot be pickled, so the test would fail there.
- `setUp` sets determinism with seed 1234. `tearDown` resets determinism to none.
- `test_shape`: string items with the module-level custom generator that yields one (character, index) tuple per character of each string item, `with_coordinates` false, batch size 3. Use 0 workers on Windows and 2 workers elsewhere. Compare sorted output and total length.
- `test_loading_array`: two 1x4x4 float images, `PatchIter` 2x2 with start position (0, 0), and RandShiftIntensity with offset 1.0 and probability 1.0. Call `set_determinism` with seed 1234 at the start of the test, before constructing the transform, the patch generator, the dataset, or any loader.
- Single-process block (num_workers 0): check the batch shape of every batch as (2, 1, 2, 2). For the final batch, check the patch values with tolerance 1e-5 and the coordinate arrays. Expected final-batch patch values are: first patch rows (1.7413, 2.7413) and (5.7413, 6.7413); second patch rows (9.1419, 10.1419) and (13.1419, 14.1419). Expected final-batch coordinates: first patch channel [0, 1], dimension 1 [0, 2], dimension 2 [2, 4]; second patch channel [0, 1], dimension 1 [2, 4], dimension 2 [2, 4].
- Two-worker block (only on non-Windows platforms): check the batch shape of every batch as (2, 1, 2, 2). For the final batch, check the coordinates with tolerance 1e-5 against the same coordinate values as the single-process block, and check the patch values with a looser tolerance (1e-3) against their own pinned two-worker values: first patch rows (2.3944, 3.3944) and (6.3944, 7.3944); second patch rows (10.6551, 11.6551) and (14.6551, 15.6551). Do not compare two-worker patch values with single-process patch values.
- Every expected value in `test_loading_array` must be a concrete numeric literal taken from the constants above. Placeholder values (empty, None, NaN, or values left to be filled in later) are not allowed, because a placeholder makes the test fail on every run.
- Do not compute expected values with a second transform instance seeded by hand, and do not call `set_random_state` on the transform between constructing the single-process DataLoader and iterating it. With zero workers, the DataLoader constructor reseeds randomizable dataset components through the seeding helper, which overwrites earlier seeding.
- Any assertion on the missing-length error message must use a literal substring check or an escaped pattern. The message contains parentheses and backticks, which are regex metacharacters; an unescaped regular expression containing them does not match the message.
- Do not place grid-dataset tests in `tests/test_patch_dataset.py`.
