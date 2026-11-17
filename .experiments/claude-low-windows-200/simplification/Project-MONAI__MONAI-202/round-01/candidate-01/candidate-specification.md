## Goals
- Make the file-writing and image-plotting logic usable without an ignite engine: an engine-free CSV saver and NIfTI saver in the data package, and an engine-free 2D/3D plot function in the visualization package.
- Keep the three ignite-facing components (segmentation saver handler, classification saver handler, TensorBoard image handler) as thin adapters. Each reads engine state through its transforms and delegates in a single call.
- Support single-item and batch saving, with optional metadata-driven naming, and keep the reference's file outputs, including the NIfTI dtype rule.

## Scope
In scope:
- New monai/data/csv_saver.py (CSV saver) and monai/data/nifti_saver.py (NIfTI saver).
- New plot function in monai/visualize/img2tensorboard.py.
- Changes to monai/handlers/segmentation_saver.py, monai/handlers/classification_saver.py, and monai/handlers/tensorboard_handlers.py.
- Default dtype of the NIfTI writer in monai/data/nifti_writer.py changed from the string form to the numpy float32 type (same value, not a behavior change).
- Renamed-parameter updates in examples/segmentation_3d/unet_evaluation_array.py, examples/segmentation_3d/unet_evaluation_dict.py, and tests/integration_sliding_window.py.
- The tests under Test requirements.
Out of scope:
- The transforms package, other handlers, and ignite attach mechanics beyond what is described here.
- New package dependencies, or any new module beyond the two data modules. Documentation pages are optional.

## Terminology
- Item: one entry along the first (batch) dimension. An item's data is channel-first.
- Batch: data whose first dimension indexes items. Batch saves iterate over it.
- Meta data mapping: a mapping with keys filename_or_obj, affine, and original_affine. In batch calls, each value is a per-item sequence indexed in parallel with the batch.
- Absent meta data: none or an empty mapping. Both behave the same: naming falls back to the item index, and no affine or original affine is used.
- Item index: a counter starting at zero, kept by each saver. It increments on every single-item save, including each item within a batch. It names items only when meta data is absent.
- Ignite-free: the module imports neither ignite nor the monai handlers package, and takes no engine object.
- Data root: never supplied by this feature, so it is treated as empty.

## Workflows
1. Classification (CSV) through the handler: when each iteration completes, the handler gets meta data from its batch transform and model output from its output transform, and calls the CSV saver's batch save once. On engine completion, it calls finalize, which writes the file. The handler does not loop over items.
2. Segmentation (NIfTI) through the handler: when each iteration completes, the handler gets meta data and output the same way, calls the NIfTI saver's batch save once, then logs one info message.
3. Standalone use: a caller constructs a saver and calls single-item or batch save. The NIfTI saver writes each item immediately. The CSV saver writes its file only when finalize is called.
4. TensorBoard image handler: on each call, compute the step from the global iteration transform. For three sources in this order, skip a source that is None; otherwise convert a tensor to numpy, require an array, and plot with the handler's index, max channels, and max frames:
   - the first element of the batch transform output, tag 'input_0';
   - the second element of the batch transform output, tag 'input_1';
   - the output transform result, tag 'output'.
   Flush the writer at the end.
5. Plot function:
   - Assert that the writer is a SummaryWriter.
   - Select the item at the index and convert a tensor to numpy.
   - Branch on the item's dimensionality:
     - Two dimensions: rescale values to 0 to 1 and write one image with suffix 'HW'.
     - Three dimensions: if the first dimension is 3 and max channels is 3, write one RGB image with suffix 'CHW'. Otherwise, if max channels is at least 1, write exactly one image: channel 0, rescaled to 0 to 1, with suffix 'HW_0', so the full tag is the tag followed by '_HW_0'. If max channels is 0, write nothing. No other image is written from this branch.
     - Four or more dimensions: flatten the leading dimensions into a list of 3D volumes. For each of the first max-channels volumes, rescale to 0 to 255 and write one animated GIF with suffix 'HWD_j', where j is the volume index, using max frames as the frame count, a scale of 1.0, and the given step.
     - Any other dimensionality: write nothing and raise no error.

## Data model
CSV cache:
- An insertion-ordered mapping from a string key to float32 values. The key is filename_or_obj when meta data is present, otherwise the string form of the item index.
- Saving with an existing key replaces its values and keeps its position.
- Finalize writes one line per key in insertion order: the key, then for each flattened value a comma and its text, then a newline. There is no header row.
- With overwrite false and an existing file, finalize first reads each row: the first column is the key, and the remaining columns are parsed as float32. File values are stored under their keys, replacing in-memory values with the same key. Merge order: keys already in memory keep their positions; keys found only in the file are appended after all in-memory keys, in file order. For example, if memory holds A and B and the file holds A and C, the written order is A, B, C, and A's value comes from the file.
- Finalize creates the output directory if it is missing.

NIfTI layout and dtype:
- For each input filename, remove the directory part and repeatedly strip extensions to get a base name. The output path is the output directory, then the base name as a folder, then the base name joined with an underscore and the output postfix, then the output extension. The input's directory part is not preserved.
- Without meta data, the item index string is the base name.
- Before writing, move each item's channel axis to the last position. Write with the affine and original affine from meta data, each optional.
- The written dtype is the saver's dtype when set, otherwise the data's own dtype. The default is none for the NIfTI saver and the segmentation handler, which keeps the model output dtype.

## API contracts
CSV saver (class CSVSaver, monai/data/csv_saver.py):
- Constructor parameters, in order: output directory (default the current directory), filename (default 'predictions.csv'), overwrite (default true). The filename must be a string ending in '.csv'. The file path is the output directory joined with the filename.
- save: the item is the first parameter, named data. The second is an optional meta data mapping, named meta_data (default none). With present meta data, the key comes from filename_or_obj; with absent meta data, the key is the string form of the item index. A tensor is detached, moved to CPU, and converted to numpy. Values are stored as float32. The item index advances by one.
- save_batch: the batch is the first parameter, named batch_data. The second is an optional meta data mapping, named meta_data (default none). For each item along the first dimension, it calls save with that item. With meta data present, each per-item mapping holds each key's value at the item's position; with meta data absent, each item uses none. The batch must be passable by the keyword batch_data as well as by position.
- finalize: takes no required argument and writes the file as described under Data model.
- No engine parameter.

NIfTI saver (class NiftiSaver, monai/data/nifti_saver.py):
- Constructor parameters, in order: output directory (default the current directory), output postfix (default 'seg'), output extension (default '.nii.gz'), dtype (default none, meaning keep the data's dtype).
- save: the item is the first parameter, named data. The second is an optional meta data mapping, named meta_data (default none), following the naming, affine, and dtype rules above. It writes through the existing NIfTI writer in monai/data/nifti_writer.py.
- save_batch: the batch is the first parameter, named batch_data. The second is an optional meta data mapping, named meta_data, with the same per-item rules as the CSV saver. The keyword batch_data must work as well as position.
- The file-name helper is a private static method with parameters postfix, input filename, output folder, and an optional data root (default empty).

Plot function (monai/visualize/img2tensorboard.py, plot_2d_or_3d_image):
- Parameters, in order: data (tensor or array in NCHW[D] layout; one item is plotted), step, writer, index (default 0), max channels (default 1), max frames (default 64), tag (default 'output').
- Accepts a tensor or a numpy array. Returns nothing.

ClassificationSaver completion hook:
- On the engine's completion event, the classification handler registers a callable that accepts the engine argument, ignores it, and calls the CSV saver's finalize with no arguments.

TensorBoard image handler (class TensorBoardImageHandler, monai/handlers/tensorboard_handlers.py):
- Constructor parameters, in order: summary writer (optional; a new writer is created if none), batch transform, output transform, global iteration transform, index (default 0; new, placed before max channels), max channels (default 1), max frames (default 64).
- Per-call behavior is as in Workflows, with the index passed for all three sources. Callable with the engine; plotting is delegated to the plot function.

Segmentation saver handler (class SegmentationSaver, monai/handlers/segmentation_saver.py):
- Constructor parameters, in order: output directory (default the current directory), output postfix (default 'seg'), output extension (default '.nii.gz'), dtype (default none), batch transform (default identity), output transform (default identity), name (optional). The former output path parameter is replaced by the output directory parameter.
- attach: sets the logger if none is set, from name or the engine's logger; registers the per-iteration hook if not already registered.
- Call: gets meta data and output, calls the NIfTI saver's batch save once, then logs.
- Holds one NIfTI saver built from the output directory, postfix, extension, and dtype.

Classification saver handler (class ClassificationSaver, monai/handlers/classification_saver.py):
- Constructor parameters, in order: output directory (default the current directory), filename (default 'predictions.csv'; new, placed before overwrite), overwrite (default true), batch transform, output transform, name.
- attach: sets the logger as above, registers the per-iteration hook, and registers the completion hook above. Attach must complete without error on the pinned ignite version.
- Call: gets meta data and output, and calls the CSV saver's batch save once.

## Module architecture
- monai/data/csv_saver.py (new): CSV saver only. Imports the standard-library file and csv modules, numpy, and torch. No ignite or monai handlers import.
- monai/data/nifti_saver.py (new): NIfTI saver. Imports numpy, torch, and the NIfTI writer in monai/data. No ignite.
- monai/visualize/img2tensorboard.py: the plot function sits beside the existing animated-GIF helpers and uses the rescale helper in monai/transforms/utils. No new visualize module.
- Segmentation and classification handlers keep their ignite imports, hold a saver, and delegate. They contain no file-writing loops and no file-name construction.
- The TensorBoard handler imports the plot function and calls it directly.
- Batch iteration belongs to the savers' batch operations; handlers make one delegating call.
- Layering: handlers depend on data and visualize; data and visualize never import handlers or ignite.

## Implementation constraints
- Savers and the plot function take no engine object. Their inputs are plain data, paths, and a SummaryWriter.
- The pinned pytorch-ignite 0.3.0 checks each handler's signature at registration. A completion handler that takes no engine argument makes attach fail. The classification handler must therefore register an engine-accepting wrapper around the CSV saver's finalize, not finalize itself, and finalize must keep taking no engine argument.
- Convert tensors to numpy (detach, move to CPU) before any numpy operation, including inside the plot function. The rescale helper requires numpy input.
- Write NIfTI files only through the existing NIfTI writer.
- The plot function must not construct its own SummaryWriter.
- Leave the existing animated-GIF helpers unchanged. Add no new dependencies.

## Dependencies
- Allowed: numpy, torch, the standard-library csv and os modules, the NIfTI writer in monai/data, the rescale helper in monai/transforms/utils, the existing tensorboard SummaryWriter, and ignite inside handler modules only.
- No new packages and no requirements or setup-file changes.
- Tests may use parameterized and the existing ignite engine.

## Naming
- The output directory parameter is named output_dir in the CSV saver, the NIfTI saver, and both handlers. The name output_path is not used.
- CSV parameter: filename. NIfTI parameters: output postfix, output extension, dtype.
- Saver method parameters: data for save, batch_data for save_batch, and meta_data for the optional mapping in both.
- The NIfTI file-name helper is private (leading underscore) and static.
- TensorBoard tags: input_0, input_1, output. Plot suffixes: HW, CHW, HW_0, HW_j, HWD_j.
- Test files: tests/test_csv_saver.py, tests/test_nifti_saver.py, tests/test_handler_segmentation_saver.py, tests/test_handler_classification_saver.py (updated), and tests/test_plot_2d_or_3d_image.py.
- Test method names use the descriptive test_ form of existing repository tests (for example test_saved_content for the CSV round-trip).

## Validation
- CSV filename: must be a string ending in '.csv', checked by assertion.
- Plot function: the writer must be a SummaryWriter, checked by assertion.
- TensorBoard handler: after tensor conversion, each non-None input, label, and output must be an array; otherwise raise ValueError with the original handler's wording for each of the three messages.
- No further validation (no checks on meta keys or data shape).

## Error handling
- A missing filename_or_obj key in meta data: let the natural key lookup failure propagate as KeyError. Do not wrap it or convert it to ValueError.
- Absent meta data (none or an empty mapping): fall back to the item index and raise nothing. An empty mapping is not treated as present meta data.
- Plot with unsupported dimensionality: write nothing and raise nothing.

## Logging
- The segmentation handler logs one info message after each batch save, with the text 'saved all the model outputs as nifti files.'
- Handler logger: a plain assignable attribute, not a computed property, set in attach to the engine's logger when none is set, or from the name argument.
- The savers and the classification handler do not log.

## Documentation
- Use Google-style docstrings with Args blocks.
- The segmentation handler's call docstring keeps the sentence that the output file datatype is determined from the engine output dtype.
- Saver docstrings describe the meta data keys and the absent-meta-data fallback to the item index.
- The CSV saver's overwrite docstring must state the actual precedence: when overwrite is false, rows loaded from an existing file replace in-memory values with the same key. It must not state the reverse.
- Docstrings must not cite export paths the package does not provide. Classes are referenced by their module.
- Documentation pages are optional.

## Maintainability
- All new and changed files, including tests and examples, must pass the repository flake8 configuration at the root, including the E-series checks (a space after every comma in call arguments and literal lists).
- Every new and changed file ends with exactly one line break after its last code line. No blank line may follow it, because the W-series check W391 is enforced and the CI lint job fails on it.
- Keep lines within the configured maximum line length.

## Compatibility
- Intended breaking changes, per the reference:
  - SegmentationSaver: the output path parameter is renamed to output_dir. The positional order becomes output directory, postfix, extension, dtype, transforms, name. The default dtype changes from the string float32 to none.
  - ClassificationSaver: filename is inserted before overwrite.
  - TensorBoardImageHandler: index is inserted before max channels.
  - The handler attributes output_dir, overwrite, output_path, output_postfix, output_ext, and dtype need not be retained.
- The in-repo callers listed under Scope use output_dir. No output_path alias is required.
- The default dtype of none keeps the model output dtype, matching the original behavior, which ignored the dtype argument.
- The default file layout and default CSV contents are unchanged.

## Behavioral acceptance criteria
- CSV: save_batch of eight zero values named testfile0 through testfile7, then finalize, writes predictions.csv with eight rows in order. Each row starts with its name, and the values are 0.
- NIfTI: save_batch of zeros shaped eight by one by two by two, named testfile0 through testfile7, creates output/testfileN/testfileN_seg.nii.gz for each N.
- NIfTI without meta data: items are named by index. Empty meta data behaves the same.
- NIfTI layout: input 'sub/case0.nii.gz' produces output/case0/case0_seg.nii.gz. The directory part is dropped.
- Dtype: a NIfTI saver with no dtype writes the data's own dtype; with a dtype set, it writes that dtype. The segmentation handler's default keeps integer output as an integer.
- Segmentation handler: attaches to an ignite engine and writes files with the layout above, using the output_dir keyword.
- Classification handler: attaches on the pinned version without error, accepts filename, and writes predictions.csv when the engine completes.
- CSV with overwrite false: rows already in the file are retained, file values replace in-memory values with the same key, and row order follows the merge rule.
- Plot: torch zero tensors shaped (1,1,10,10), (1,3,10,10), (1,4,10,10), (1,1,10,10,10), and (1,3,10,10,10) each plot without error and create the run output. Tensor input is accepted.
- Plot, three-dimensional non-RGB item: exactly one image is written, for channel 0, with suffix HW_0. With max channels 0, no image is written.
- TensorBoard handler: the index selects which batch element is plotted.
- Keyword calls: save_batch with batch_data and save with data succeed on both the CSV and NIfTI savers.

## Test requirements
- Each of the five test files exists and follows repository style: unittest, parameterized for shape cases, and temporary directories removed after each test.
- Expected paths match the layout rules. Tests must not assert specific pixel values for constant input; they check that output exists.
- Plot tests for three-dimensional single-channel input assert the tag name followed by '_HW_0' (for example input_0_HW_0), not '_HW'.
- A plot test with three-dimensional non-RGB input and max channels 0 asserts that no image is written.
- The overwrite-false CSV test asserts that file values replace in-memory values for shared keys and that row order follows the merge rule. Its expectations must not contradict that rule.
- The updated classification handler test passes filename.
- The integration sliding-window test uses output_dir.
- Tests describe behavior and are not claimed to pass unless executed.
