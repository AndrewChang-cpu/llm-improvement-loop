## Goals
- Make file writing and image plotting usable without an ignite engine: a CSV saver and a NIfTI saver in the data package, and a 2D/3D plot function in the visualization package.
- Keep the three ignite-facing components (segmentation saver handler, classification saver handler, TensorBoard image handler) as thin adapters that read engine state through transforms and delegate in one call.
- Support single-item and batch saving, optional metadata-driven naming, and the constructor options below.
- Keep the reference file outputs, including the NIfTI dtype rule.

## Scope
In scope:
- New modules monai/data/csv_saver.py and monai/data/nifti_saver.py.
- New plot function in monai/visualize/img2tensorboard.py.
- Changes to monai/handlers/segmentation_saver.py, monai/handlers/classification_saver.py, and monai/handlers/tensorboard_handlers.py.
- Changing the NIfTI writer default dtype in monai/data/nifti_writer.py from the string form to the numpy float32 type. The value is identical, so behavior does not change.
- Updating in-repo callers of the renamed parameter: examples/segmentation_3d/unet_evaluation_array.py, examples/segmentation_3d/unet_evaluation_dict.py, and tests/integration_sliding_window.py.
- The tests under Test requirements.
Out of scope: transforms, other handlers, ignite attach mechanics beyond this description, new dependencies, and other new modules.

## Terminology
- Item: one entry along the first (batch) dimension, channel-first.
- Batch: data whose first dimension indexes items. Batch operations iterate over it.
- Meta data mapping: keys filename_or_obj, affine, and original_affine. In batch calls each value is a per-item sequence, indexed in parallel with the batch.
- Absent meta data: none or an empty mapping. Both name items by item index and use no affine or original affine.
- Item index: a counter starting at zero, kept by each saver. It increments on every single-item save, including each item within a batch, and names items only when meta data is absent.
- Ignite-free: the module imports neither ignite nor the handlers package and takes no engine object.
- Data root: optional root preserving relative folder structure. This feature never supplies one, so it is empty.

## Workflows
1. Classification (CSV) through the handler: each completed iteration, the handler gets meta data from its batch transform and model output from its output transform, and calls the CSV saver's batch save once. On the completion event, it calls finalize, which writes the file. The handler does not loop over items.
2. Segmentation (NIfTI) through the handler: each completed iteration, the handler gets meta data and output the same way, calls the NIfTI saver's batch save once, then logs.
3. Standalone: a caller constructs a saver and calls single-item or batch save. The NIfTI saver writes each item immediately. The CSV saver writes its file only when finalize is called.
4. TensorBoard image handler: on each call, compute the step from the global iteration transform. Then, for three sources in this order, skip a source that is None. Otherwise convert a tensor to numpy, require an array, and plot with the handler's index, max channels, and max frames:
   - the first element of the batch transform output, tag 'input_0';
   - the second element of the batch transform output, tag 'input_1';
   - the output transform result, tag 'output'.
   Flush the writer at the end.

## Data model
CSV cache:
- The CSV saver keeps an insertion-ordered mapping from a string key to a float32 array. The key is the filename_or_obj value when meta data is present, otherwise the string form of the item index.
- Saving with an existing key replaces its values and keeps its position.
- Finalize writes one line per key in insertion order: the key, then for each flattened value a comma and the value's text, then a newline. There is no header row.
- With overwrite false and an existing file, finalize first reads each row: the first column is the key, and the rest parse as float32. File values replace in-memory values with the same key. In-memory keys keep their positions; file-only keys are appended after all in-memory keys, in file order. Example: memory holds A and B, the file holds A and C; the written order is A, B, C, with A's file value.
- Finalize creates the output directory if it is missing.

NIfTI output layout and dtype:
- For each input filename, remove the directory part and repeatedly strip extensions to get a base name. The output path is the output directory, then the base name as a folder, then the base name joined with an underscore and the postfix, then the extension. The input's directory part is not preserved.
- Without meta data, the item index string is the base name.
- Before writing, move each item's channel axis to the last position. Write with the affine and original affine from meta data, each optional.
- The written dtype is the saver's dtype when set, otherwise the data's own dtype.

## API contracts
Parameters are listed in order, with defaults in parentheses.

CSV saver (class CSVSaver, monai/data/csv_saver.py):
- Constructor: output directory (current directory), filename ('predictions.csv'), overwrite (true). The filename must be a string ending in '.csv'. The file path is the output directory joined with the filename.
- save: data; meta_data (optional, default none). Present meta data gives the key from filename_or_obj; absent meta data uses the string form of the item index. A tensor is detached, moved to CPU, and converted to numpy. Values are stored as float32. The item index advances by one.
- save_batch: batch_data; meta_data (optional, default none). For each item along the first dimension, it calls save with that item. With present meta data, each per-item mapping holds each key's value at the item's position. With absent meta data, each item uses none. Both batch_data and data must be accepted as keyword arguments.
- finalize: no required argument. Writes the file as described under Data model.
- No engine parameter.

NIfTI saver (class NiftiSaver, monai/data/nifti_saver.py):
- Constructor: output directory (current directory), output postfix ('seg'), output extension ('.nii.gz'), dtype (none, meaning keep the data's dtype).
- save: data; meta_data (optional, default none), with the naming, affine, and dtype rules above. Writes through the existing NIfTI writer in monai/data/nifti_writer.py.
- save_batch: batch_data; meta_data (optional, default none), with the same per-item rules as the CSV saver. Accepts batch_data as a keyword argument.
- The file-name helper is a private static method with parameters postfix, input filename, output folder, and an optional data root (default empty).

Plot function (monai/visualize/img2tensorboard.py, plot_2d_or_3d_image):
- Parameters in order: data (tensor or array in NCHW[D] layout; one item is plotted), step, writer, index (0), max channels (1), max frames (64), tag ('output'). Accepts a tensor or numpy array. Returns nothing.
- Assert that the writer is a SummaryWriter. Select the item at the index and convert a tensor to numpy. Branch on the item's dimensionality:
  - Two dimensions: rescale values to 0 to 1 and write one image with suffix 'HW'.
  - Three dimensions: if the first dimension is 3 and max channels is 3, write one RGB image with suffix 'CHW'. Otherwise, if max channels is at least 1, write exactly one image, the first channel rescaled to 0 to 1, with suffix 'HW_0' (full tag: the tag followed by '_HW_0'). If max channels is 0, write nothing.
  - Four or more dimensions: flatten the leading dimensions into a list of 3D volumes. For each of the first max-channels volumes, rescale to 0 to 255 and write one animated GIF with suffix 'HWD_j', where j is the volume index, using max frames as the frame count, a scale of 1.0, and the given step.
  - Any other dimensionality: write nothing and raise no error.

ClassificationSaver completion hook:
- On the engine's completion event, the handler registers a callable that accepts the engine argument, ignores it, and calls the CSV saver's finalize with no arguments.

TensorBoard image handler (class TensorBoardImageHandler, monai/handlers/tensorboard_handlers.py):
- Constructor: summary writer (optional; a new writer is created if none), batch transform, output transform, global iteration transform, index (0), max channels (1), max frames (64). Index is new and sits before max channels.
- Per-call behavior is as in Workflows. The index is passed to the plot function for all three sources. Callable with the engine; plotting is delegated.

Segmentation saver handler (class SegmentationSaver, monai/handlers/segmentation_saver.py):
- Constructor: output directory (current directory), output postfix ('seg'), output extension ('.nii.gz'), dtype (none), batch transform (identity), output transform (identity), name (optional). Output directory replaces the former output path parameter.
- attach: sets the logger if none is set, from name or the engine's logger. Registers the per-iteration hook if not already registered.
- Call: gets meta data and output, calls the NIfTI saver's batch save once, then logs.
- Holds one NIfTI saver built from output directory, postfix, extension, and dtype.

Classification saver handler (class ClassificationSaver, monai/handlers/classification_saver.py):
- Constructor: output directory (current directory), filename ('predictions.csv'), overwrite (true), batch transform, output transform, name. Filename is new and sits before overwrite.
- attach: sets the logger as above, registers the per-iteration hook and the completion hook. Attach must complete without error on the pinned ignite version.
- Call: gets meta data and output, and calls the CSV saver's batch save once.

## Module architecture
- monai/data/csv_saver.py (new): standard-library csv and file modules, numpy, and torch.
- monai/data/nifti_saver.py (new): numpy, torch, and the NIfTI writer in monai/data.
- monai/visualize/img2tensorboard.py: the plot function sits beside the existing animated-GIF helpers and uses the rescale helper in monai/transforms/utils.
- Segmentation and classification handler modules keep their ignite imports, hold a saver, and delegate. They contain no file-writing loops and no file-name construction.
- monai/handlers/tensorboard_handlers.py imports the plot function and calls it directly.
- Batch iteration belongs to the savers. Handlers make one delegating call.
- Handlers depend on data and visualize. Data and visualize never import handlers or ignite.

## Implementation constraints
- Savers and the plot function take no engine object. Their inputs are plain data, paths, and a SummaryWriter.
- The pinned ignite version (pytorch-ignite 0.3.0) checks each handler's signature at registration, and a completion handler without an engine argument makes attach fail. The classification handler therefore registers an engine-accepting wrapper around finalize; finalize itself takes no engine argument.
- Convert tensors to numpy (detach, move to CPU) before any numpy operation, including inside the plot function. The rescale helper requires numpy input.
- Write NIfTI files only through the existing NIfTI writer.
- The plot function must not construct its own SummaryWriter. Leave the existing animated-GIF helpers unchanged.
- No new packages and no requirements or setup-file changes. Allowed imports: numpy, torch, standard-library csv and os, the NIfTI writer, the rescale helper, the tensorboard SummaryWriter, and ignite inside handler modules only.

## Naming
- The output directory parameter is output_dir in the CSV saver, NIfTI saver, segmentation handler, and classification handler. output_path is not used.
- CSV parameter: filename. NIfTI parameters: output postfix, output extension, dtype.
- Saver method parameters: data for save, batch_data for save_batch, meta_data for the optional mapping in both.
- The NIfTI file-name helper is private and static.
- TensorBoard tags: input_0, input_1, output. Plot suffixes: HW, CHW, HW_0, HWD_j.
- Test files: tests/test_csv_saver.py, tests/test_nifti_saver.py, tests/test_handler_segmentation_saver.py, tests/test_handler_classification_saver.py (updated), tests/test_plot_2d_or_3d_image.py. Test method names follow the descriptive test_ form of existing tests, such as test_saved_content.

## Validation
- CSV filename: a string ending in '.csv', checked by assertion.
- Plot function: the writer must be a SummaryWriter, checked by assertion.
- TensorBoard handler: after tensor conversion, each non-None input, label, and output must be an array; otherwise raise ValueError with the original handler's wording for each of the three messages.
- No further validation, such as checks on meta keys or data shape.

## Error handling
- A missing filename_or_obj key in meta data: let the KeyError propagate. Do not wrap it or convert it to ValueError.
- Absent meta data (none or empty mapping) falls back to the item index without raising.
- Plot with unsupported dimensionality: write nothing and raise nothing.

## Logging
- The segmentation handler logs one info message after each batch save: 'saved all the model outputs as nifti files.'
- The handler logger is a plain attribute, set in attach to the engine's logger when none is set, or from the name argument.
- The savers and the classification handler do not log.

## Documentation
- Use Google-style docstrings with Args blocks.
- The segmentation handler's call docstring keeps the sentence that the output file datatype is determined from the engine output dtype.
- Saver docstrings describe the meta data keys and the item-index fallback.
- The CSV saver's overwrite docstring states the precedence: when overwrite is false, rows loaded from an existing file replace in-memory values with the same key.
- Do not cite export paths the package does not provide. Reference classes by their module.

## Maintainability
- All new and changed files, including tests and examples, must pass the root flake8 configuration, including E-series checks. Put a space after every comma in call arguments and list literals.
- Each new and changed file ends with exactly one line break after its last code line, with no blank line after it (CI fails on W391).

## Compatibility
- Intended breaking changes:
  - SegmentationSaver: output path renamed to output_dir. Positional order becomes output directory, postfix, extension, dtype, transforms, name. Default dtype changes from the string float32 to none.
  - ClassificationSaver: filename is inserted before overwrite.
  - TensorBoardImageHandler: index is inserted before max channels.
  - Handler attributes output_dir, overwrite, output_path, output_postfix, output_ext, and dtype need not be retained.
- In-repo callers use output_dir; no output_path alias is required.
- The default dtype of none keeps the model output dtype, matching the original behavior. The default file layout and CSV contents are unchanged.

## Behavioral acceptance criteria
- CSV: save_batch of eight zeros named testfile0 through testfile7, then finalize, writes predictions.csv with eight rows in order, each starting with its name.
- NIfTI: save_batch of zeros shaped eight by one by two by two, named testfile0 through testfile7, creates output/testfileN/testfileN_seg.nii.gz for each N.
- NIfTI without meta data names items by index; empty meta data behaves the same way.
- Input 'sub/case0.nii.gz' produces output/case0/case0_seg.nii.gz.
- Dtype: with no dtype, a NIfTI saver writes the data's dtype; with a dtype set, it writes that dtype. The segmentation handler's default keeps an integer output as an integer.
- Segmentation handler: attaches to an ignite engine and writes files with the layout above, using the output_dir keyword.
- Classification handler: attaches on the pinned version, accepts filename, and writes predictions.csv when the engine completes.
- CSV with overwrite false: retained file rows, file values replacing in-memory values for shared keys, and the merge order under Data model.
- Plot: torch zero tensors shaped (1,1,10,10), (1,3,10,10), (1,4,10,10), (1,1,10,10,10), and (1,3,10,10,10) each plot without error and create the run output. Tensor input is accepted.
- Plot, three-dimensional non-RGB item: exactly one image, for channel 0, with suffix HW_0. With max channels 0, no image is written.
- TensorBoard handler: index selects which batch element is plotted.

## Test requirements
- Each of the five test files exists and follows repository style: unittest, parameterized for shape cases, and temporary directories removed after each test.
- Expected paths match the layout rules under Data model. Tests check that output exists for constant input rather than asserting pixel values.
- Plot tests for three-dimensional single-channel input assert the tag followed by '_HW_0' (for example input_0_HW_0). A three-dimensional non-RGB test with max channels 0 asserts that no image is written.
- The overwrite-false CSV test asserts that file values replace in-memory values for shared keys and that row order follows the merge rule.
- The updated classification test passes filename. The integration sliding-window test uses output_dir.
- Tests describe behavior and are not claimed to pass unless executed.
