## Goals
- Make the file-writing and image-plotting logic usable without an ignite engine. Provide an engine-free CSV saver and NIfTI saver in the data package, and an engine-free 2D/3D plotting function in the visualization package.
- Keep the three ignite-facing components (segmentation saver handler, classification saver handler, TensorBoard image handler) as thin adapters. Each reads engine state through its transforms, then delegates in a single call.
- Support single-item and batch saving, with optional metadata-driven naming, and keep the file outputs the reference defines, including the NIfTI dtype rule.

## Scope
In scope:
- New module monai/data/csv_saver.py (CSV saver).
- New module monai/data/nifti_saver.py (NIfTI saver).
- New plotting function in monai/visualize/img2tensorboard.py.
- Changes to monai/handlers/segmentation_saver.py, monai/handlers/classification_saver.py, and monai/handlers/tensorboard_handlers.py.
- Changing the default dtype argument of the NIfTI writer in monai/data/nifti_writer.py from the string form to the numpy float32 type. The value is the same, so this is not a behavior change.
- Updating in-repo callers of the renamed parameter: examples/segmentation_3d/unet_evaluation_array.py, examples/segmentation_3d/unet_evaluation_dict.py, and tests/integration_sliding_window.py.
- The tests listed under Test requirements.
Out of scope: transforms package changes, other handlers, ignite attach and event-registration mechanics beyond what is described here, new dependencies, and new modules beyond the two data modules.

## Terminology
- Item: one entry along the first (batch) dimension. Each item is channel-first (channels, then spatial dimensions).
- Batch: data whose first dimension indexes items. Batch operations iterate over it.
- Meta data mapping: a mapping whose keys hold per-item values. The keys used are filename_or_obj, affine, and original_affine. In batch calls each value is a per-item sequence, indexed in parallel with the batch.
- Absent meta data: meta data that is none or an empty mapping. Both behave the same: naming falls back to the item index, and no affine or original affine is used.
- Item index: a running counter starting at zero, kept by each saver. It increments on every single-item save, including each item within a batch. It names items only when meta data is absent.
- Ignite-free: the module imports neither ignite nor the monai handlers package, and takes no engine object.
- Data root: an optional root directory for preserving relative folder structure. This feature never supplies one, so it is treated as empty.

## Workflows
1. Classification (CSV) through the handler: on each completed iteration, the handler gets meta data from its batch transform and model output from its output transform, and calls the CSV saver's batch save once. On the completion event, it calls the saver's finalize, which writes the file. The handler does not loop over items.
2. Segmentation (NIfTI) through the handler: on each completed iteration, the handler gets meta data and output the same way and calls the NIfTI saver's batch save once, then logs one info message.
3. Standalone use: a caller constructs either saver directly and calls single-item or batch save. The NIfTI saver writes each item immediately. The CSV saver writes its file only when finalize is called.
4. TensorBoard image handler: on each call, compute the step from the global iteration transform. Then, for three sources in this order, skip the source if it is None. Otherwise convert a tensor to numpy, require an array, and plot with the handler's index, max channels, and max frames:
   - the first element of the batch transform output, tag 'input_0';
   - the second element of the batch transform output, tag 'input_1';
   - the output transform result, tag 'output'.
   Flush the writer at the end.
5. Plot function:
   - Assert that the writer is a SummaryWriter.
   - Select the item at the index, and convert a tensor to numpy.
   - Branch on the item's dimensionality:
     - Two dimensions: rescale values to 0 to 1 and write one image with the suffix 'HW'.
     - Three dimensions: if the first dimension is 3 and max channels is 3, write one RGB image with the suffix 'CHW'. Otherwise, if max channels is at least 1, write exactly one image: channel 0, rescaled to 0 to 1, with the suffix 'HW_0', so the full tag is the tag followed by '_HW_0'. If max channels is 0, write nothing. No other image comes from this branch.
     - Four or more dimensions: flatten the leading dimensions into a list of 3D volumes. For each of the first max-channels volumes, rescale to 0 to 255 and write one animated GIF with the suffix 'HWD_j', where j is the volume index, using max frames as the frame count, a scale of 1.0, and the given step.
     - Any other dimensionality: write nothing and raise no error.

## Data model
CSV cache:
- The CSV saver holds an insertion-ordered mapping from a string key to a float32 array of values. The key is the filename_or_obj value when meta data is present, otherwise the string form of the item index.
- Saving with an existing key replaces its values and keeps its original position.
- Finalize writes one line per key, in insertion order: the key, then for each flattened value a comma and the value's text, then a newline. There is no header row.
- With overwrite false and an existing file, finalize first reads each existing row: the first column is the key and the remaining columns are parsed as float32. File values replace in-memory values with the same key. Merge order: keys already in memory keep their position, and keys found only in the file are appended after all in-memory keys, in file order. For example, if memory holds A and B and the file holds A and C, the written order is A, B, C, and A has the file's value. Then the merged cache is written.
- Finalize creates the output directory if it is missing.

NIfTI output layout and dtype:
- For each input filename, remove the directory part, then repeatedly strip extensions until none remain, giving a base name. The output path is the output directory, the base name as a folder, then the base name joined with an underscore and the output postfix, then the output extension. The input directory is not preserved.
- Without meta data, the item index string is the base name.
- Before writing, move each item's channel axis to the last position. Write using the affine and original affine from meta data, each optional and absent when not given.
- The written dtype is the saver's dtype when set, otherwise the data's own dtype. The default is none for the NIfTI saver and the segmentation handler, which keeps the model output dtype.

## API contracts
CSV saver (class CSVSaver in monai/data/csv_saver.py):
- Constructor parameters, in order: output directory (default the current directory), filename (default 'predictions.csv'), overwrite (default true). The filename must be a string ending in '.csv'. The file path is the output directory joined with the filename.
- save: the item is the first parameter, named data. The second parameter is an optional meta data mapping, named meta_data (default none). With present meta data, the key comes from filename_or_obj. With absent meta data, the key is the string form of the item index. A tensor is detached, moved to CPU, and converted to numpy. Values are stored as float32. The item index advances by one.
- save_batch: the batch is the first parameter, named batch_data, with the optional meta_data second. It calls save for each item along the first dimension. With present meta data, each key's per-item value is taken at the item's position. With absent meta data, each item uses none. The batch must be accepted by keyword batch_data as well as by position.
- finalize: takes no required argument and writes the file as described under Data model.
- No engine parameter.

NIfTI saver (class NiftiSaver in monai/data/nifti_saver.py):
- Constructor parameters, in order: output directory (default the current directory), output postfix (default 'seg'), output extension (default '.nii.gz'), dtype (default none, meaning keep the data's dtype).
- save: the item is the first parameter, named data. The second parameter is the optional meta_data mapping (default none), following the naming, affine, and dtype rules above. It writes through the existing NIfTI writer function in monai/data/nifti_writer.py.
- save_batch: the batch is the first parameter, named batch_data, with the optional meta_data second and the same per-item rules as the CSV saver. The batch must be accepted by keyword batch_data as well as by position.
- The file-name helper is a private static method with the parameters postfix, input filename, output folder, and an optional data root (default empty).

Plot function (monai/visualize/img2tensorboard.py, named plot_2d_or_3d_image):
- Parameters, in order: data (tensor or array in NCHW[D] layout; one item is plotted), step, writer, index (default 0), max channels (default 1), max frames (default 64), tag (default 'output').
- Accepts a tensor or numpy array. Returns nothing.

ClassificationSaver completion hook:
- The classification handler registers, on the engine's completion event, a callable that accepts the engine argument and calls the CSV saver's finalize with no arguments. The engine argument is ignored.

TensorBoard image handler (class TensorBoardImageHandler in monai/handlers/tensorboard_handlers.py):
- Constructor parameters, in order: summary writer (optional; a new writer is created if none), batch transform, output transform, global iteration transform, index (default 0), max channels (default 1), max frames (default 64). The index parameter is new and sits before max channels.
- Per-call behavior is as in Workflows. The index is passed to the plot function for all three sources.
- Callable with the engine. Plotting is delegated to the plot function.

Segmentation saver handler (class SegmentationSaver in monai/handlers/segmentation_saver.py):
- Constructor parameters, in order: output directory (default the current directory), output postfix (default 'seg'), output extension (default '.nii.gz'), dtype (default none), batch transform (default identity), output transform (default identity), name (optional). The former output path parameter is replaced by the output directory parameter.
- attach: sets the logger if none is set, from name or the engine's logger. Registers the per-iteration hook if not already registered.
- Call: gets meta data and output, calls the NIfTI saver's batch save once, then logs.
- Holds one NIfTI saver built from the output directory, postfix, extension, and dtype.

Classification saver handler (class ClassificationSaver in monai/handlers/classification_saver.py):
- Constructor parameters, in order: output directory (default the current directory), filename (default 'predictions.csv'), overwrite (default true), batch transform, output transform, name. The filename parameter is new and sits before overwrite.
- attach: sets the logger as above, registers the per-iteration hook, and registers the completion hook. It must complete without error on the pinned ignite version.
- Call: gets meta data and output, and calls the CSV saver's batch save once.

## Module architecture
- monai/data/csv_saver.py (new): CSV saver only. Imports the standard-library file and csv modules, numpy, and torch.
- monai/data/nifti_saver.py (new): NIfTI saver. Imports numpy, torch, and the NIfTI writer in monai/data.
- monai/visualize/img2tensorboard.py: holds the plot function next to the existing animated-GIF helpers, and uses the rescale helper in monai/transforms/utils. No new visualize module.
- monai/handlers/segmentation_saver.py and classification_saver.py: keep the ignite imports, hold a saver instance, and delegate. They contain no file-writing loops and no file-name construction.
- monai/handlers/tensorboard_handlers.py: imports the plot function and calls it directly.
- Batch iteration belongs to the savers' batch operations. Handlers make one delegating call.
- Layering: handlers depend on data and visualize. Data and visualize never import handlers or ignite.

## Implementation constraints
- Savers and the plot function take no engine object. Their inputs are plain data, paths, and a SummaryWriter.
- The pinned ignite version (pytorch-ignite 0.3.0) checks each handler's signature at registration. A completion handler without an engine argument makes attach fail. So the classification handler registers an engine-accepting wrapper around the CSV saver's finalize, not finalize itself. The CSV saver's finalize keeps taking no engine argument.
- Convert tensors to numpy (detach, move to CPU) before any numpy operation, including inside the plot function. The rescale helper requires numpy input.
- Write NIfTI files only through the existing NIfTI writer.
- The plot function must not construct its own SummaryWriter.
- Leave the existing animated-GIF helpers unchanged.
- Add no new dependencies, and make no requirements or setup-file changes.

## Dependencies
- Allowed: numpy, torch, the standard-library csv and os modules, the NIfTI writer in monai/data, the rescale helper in monai/transforms/utils, the existing tensorboard SummaryWriter, and ignite inside handler modules only.
- Tests may use parameterized and the existing ignite engine.

## Naming
- The output directory parameter is named output_dir in the CSV saver, NIfTI saver, segmentation handler, and classification handler. output_path is not used.
- CSV parameter: filename. NIfTI parameters: output postfix, output extension, dtype.
- Saver method parameters: data for save, batch_data for save_batch, and meta_data for the optional mapping in both.
- The NIfTI file-name helper is private (leading underscore) and static.
- TensorBoard tags: input_0, input_1, output. Plot suffixes: HW, CHW, HW_0, HW_j, HWD_j.
- Test files: tests/test_csv_saver.py, tests/test_nifti_saver.py, tests/test_handler_segmentation_saver.py, tests/test_handler_classification_saver.py (updated), tests/test_plot_2d_or_3d_image.py.
- Test method names use the descriptive test_ form of existing repository tests (for example test_saved_content for the CSV round-trip).

## Validation
- CSV filename: must be a string ending in '.csv', checked by assertion.
- Plot function: the writer must be a SummaryWriter, checked by assertion.
- TensorBoard handler: after tensor conversion, each non-None input, label, and output must be an array. Otherwise raise ValueError, using the original handler's wording for each of the three messages.
- Add no further validation (no checks on meta keys or data shape).

## Error handling
- A missing filename_or_obj key in meta data: let the natural key lookup failure propagate as KeyError. Do not wrap it or convert it to ValueError.
- Absent meta data (none or an empty mapping): fall back to the item index and raise nothing. An empty mapping is not treated as present meta data.
- Plot with unsupported dimensionality: write nothing and raise nothing.

## Logging
- The segmentation handler logs one info message after each batch save, with the text 'saved all the model outputs as nifti files.'.
- Handler logger: a plain assignable attribute, not a computed property. Set in attach to the engine's logger when none is set, or from the name argument.
- The savers and the classification handler do not log.

## Documentation
- Use Google-style docstrings with Args blocks, following the repository convention.
- The segmentation handler's call docstring keeps the sentence that the output file datatype is determined from the engine output dtype.
- Saver docstrings describe the meta data keys and the fallback to the item index for absent meta data (none or empty).
- The CSV saver's overwrite docstring must state the actual precedence: when overwrite is false, rows loaded from an existing file replace in-memory values with the same key.
- Docstrings must not cite export paths the package does not provide. Classes are referenced by their module.

## Maintainability
- All new and changed files, including tests and examples, must pass the repository's flake8 configuration at the repository root, including the E-series checks (a space after every comma in call arguments and literal lists).
- Every new and changed file ends with exactly one line break after its last code line. No blank line may follow it, because the W391 trailing-blank-line check is selected and the CI lint job fails on it.
- Keep lines within the configured maximum line length.

## Compatibility
- Intended breaking changes, per the reference:
  - SegmentationSaver: the output path parameter is renamed to output_dir. The positional order becomes output directory, postfix, extension, dtype, transforms, name. The default dtype changes from the string float32 to none.
  - ClassificationSaver: a filename parameter is inserted before overwrite.
  - TensorBoardImageHandler: an index parameter is inserted before max channels.
  - The handler attributes output_dir, overwrite, output_path, output_postfix, output_ext, and dtype need not be retained.
- In-repo callers use output_dir. No output_path alias is required.
- The default dtype of none keeps the model output dtype, matching the original behavior, which ignored the dtype argument.
- The default file layout and CSV contents for the default path are unchanged.

## Behavioral acceptance criteria
- CSV: save_batch of eight zero values with names testfile0 through testfile7, then finalize, writes predictions.csv with eight rows in order. Each row starts with its name, and the values are 0.
- NIfTI: save_batch of zeros with shape eight by one by two by two, with names testfile0 through testfile7, creates output/testfileN/testfileN_seg.nii.gz for each N.
- NIfTI without meta data: items are named by index. Empty meta data behaves the same way.
- NIfTI path layout: input 'sub/case0.nii.gz' produces output/case0/case0_seg.nii.gz.
- Dtype: a NIfTI saver with no dtype writes the data's own dtype. With a dtype set, it writes that dtype. The segmentation handler's default keeps an integer output as an integer.
- Segmentation handler: attaches to an ignite engine and writes files with the layout above, using the output_dir keyword.
- Classification handler: attaches to an ignite engine on the pinned version without error, accepts filename, and writes predictions.csv when the engine completes.
- CSV with overwrite false: rows already in the file are retained, file values replace in-memory values with the same key, and row order follows the merge rule.
- Plot: torch zero tensors with shapes (1,1,10,10), (1,3,10,10), (1,4,10,10), (1,1,10,10,10), and (1,3,10,10,10) each plot without error and create the run output. Tensor input is accepted.
- Plot, three-dimensional non-RGB item: exactly one image is written, for channel 0, with suffix HW_0. With max channels 0, no image is written.
- TensorBoard handler: the index selects which batch element is plotted.
- Keyword calls: save_batch with batch_data and save with data succeed on both the CSV saver and the NIfTI saver.

## Test requirements
- Each of the five test files under Naming exists and follows repository style: unittest, parameterized for shape cases, and temporary directories removed after each test.
- Expected paths match the layout rules under Data model. Tests must not assert pixel values for constant input; they check that output exists.
- Plot tests for three-dimensional single-channel input assert the tag followed by '_HW_0' (for example input_0_HW_0), not '_HW'.
- A plot test with three-dimensional non-RGB input and max channels 0 asserts that no image is written.
- The overwrite-false CSV test asserts that file values replace in-memory values for shared keys and that row order follows the merge rule.
- The updated classification handler test passes filename. The integration sliding-window test uses output_dir.
