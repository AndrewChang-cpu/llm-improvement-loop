## Goals
- Make file writing and image plotting usable without an ignite engine: an engine-free CSV saver and NIfTI saver in the data package, and an engine-free 2D/3D plot function in the visualization package.
- Keep the three ignite-facing components (segmentation saver handler, classification saver handler, TensorBoard image handler) as thin adapters that read engine state through transforms and delegate in one call.
- Support single-item and batch saving, optional metadata-driven naming, and the constructor options below, keeping the reference file outputs.

## Scope
In scope:
- New modules monai/data/csv_saver.py and monai/data/nifti_saver.py, and a new plot function in monai/visualize/img2tensorboard.py.
- Changes to monai/handlers/segmentation_saver.py, monai/handlers/classification_saver.py, and monai/handlers/tensorboard_handlers.py.
- Changing the NIfTI writer default dtype in monai/data/nifti_writer.py from the string form to the numpy float32 type. The value is identical.
- Updating in-repo callers of the renamed parameter: examples/segmentation_3d/unet_evaluation_array.py, examples/segmentation_3d/unet_evaluation_dict.py, and tests/integration_sliding_window.py.
Out of scope: transforms, other handlers, new dependencies, and new modules beyond the two data modules.

## Terminology
- Item: one entry along the first (batch) dimension, channel-first. Batch: data whose first dimension indexes items.
- Meta data mapping: keys filename_or_obj, affine, and original_affine. In batch calls each value is a per-item sequence, indexed in parallel with the batch.
- Absent meta data: none or an empty mapping. Naming falls back to the item index, and no affine or original affine is used.
- Item index: a counter starting at zero, kept by each saver. It increments on every single-item save, including each batch item, and names items only when meta data is absent.
- Ignite-free: the module imports neither ignite nor the handlers package and takes no engine object.

## Workflows
1. Classification (CSV) through the handler: each completed iteration, the handler gets meta data from its batch transform and model output from its output transform, and calls the CSV saver's batch save once. On the completion event, it calls finalize, which writes the file.
2. Segmentation (NIfTI) through the handler: each completed iteration, the handler gets meta data and output the same way, calls the NIfTI saver's batch save once, then logs one info message.
3. Standalone use: a caller constructs a saver directly and calls save or save_batch. The NIfTI saver writes each item immediately; the CSV saver writes only when finalize is called.
4. TensorBoard image handler: on each call, compute the step from the global iteration transform. For three sources in this order, skip a source that is None; otherwise convert a tensor to numpy, require an array, and plot with the handler's index, max channels, and max frames:
   - the first element of the batch transform output, tag 'input_0';
   - the second element of the batch transform output, tag 'input_1';
   - the output transform result, tag 'output'.
   Flush the writer at the end.
5. Plot function:
   - Assert that the writer is a SummaryWriter. Select the item at the index and convert a tensor to numpy.
   - Two dimensions: rescale values to 0 to 1 and write one image with suffix 'HW'.
   - Three dimensions: if the first dimension is 3 and max channels is 3, write one RGB image with suffix 'CHW'. Otherwise, if max channels is at least 1, write exactly one image, channel 0 rescaled to 0 to 1, with suffix 'HW_0'. If max channels is 0, write nothing.
   - Four or more dimensions: flatten the leading dimensions into a list of 3D volumes. For each of the first max-channels volumes, rescale to 0 to 255 and write one animated GIF with suffix 'HWD_j', where j is the volume index, using max frames as the frame count, a scale of 1.0, and the given step.
   - Any other dimensionality: write nothing and raise no error.

## Data model
CSV cache:
- An insertion-ordered mapping from a string key to a float32 array of values. The key is the filename_or_obj value when meta data is present, otherwise the string form of the item index.
- Saving with an existing key replaces its values and keeps its position.
- Finalize writes one line per key, in insertion order: the key, a comma, each flattened value's text, then a newline. There is no header row. Finalize creates the output directory if missing.
- With overwrite false and an existing file, finalize first reads each row: the first column is the key, and the rest parse as float32. File values replace in-memory values with the same key. Keys already in memory keep their positions; keys found only in the file are appended after all in-memory keys, in file order. Example: memory holds A and B, the file holds A and C; the written order is A, B, C, and A's value is the file's value.

NIfTI output layout and dtype:
- For each input filename, remove the directory part and repeatedly strip extensions to get a base name. The output path is the output directory, then the base name as a folder, then the base name joined with an underscore and the postfix, then the extension. The input's directory part is not preserved.
- Without meta data, the item index string is the base name.
- Before writing, move each item's channel axis to the last position. Write with the affine and original affine from meta data, each optional.
- The written dtype is the saver's dtype when set, otherwise the data's own dtype.

## API contracts
Parameters are listed in order, with defaults in parentheses.

CSV saver (CSVSaver, monai/data/csv_saver.py):
- Constructor: output directory (current directory), filename ('predictions.csv'), overwrite (true). The filename must be a string ending in '.csv'. The file path is the output directory joined with the filename.
- save: data; meta_data (optional, default none). With present meta data, the key comes from filename_or_obj. Otherwise the key is the string form of the item index. A tensor is detached, moved to CPU, and converted to numpy. Values are stored as float32. The item index advances by one.
- save_batch: batch_data; meta_data (optional, default none). For each item along the first dimension, it calls save with that item and its per-item mapping, or none when meta data is absent. Both arguments must be passable by keyword.
- finalize: no required argument. Writes the file as described under Data model. No engine parameter.

NIfTI saver (NiftiSaver, monai/data/nifti_saver.py):
- Constructor: output directory (current directory), output postfix ('seg'), output extension ('.nii.gz'), dtype (none, meaning keep the data's dtype).
- save: data; meta_data (optional, default none), with the naming, affine, and dtype rules above. Writes through the existing NIfTI writer in monai/data/nifti_writer.py.
- save_batch: batch_data; meta_data (optional, default none), with the same per-item rules as the CSV saver. Both arguments must be passable by keyword.
- The file-name helper is a private static method with parameters postfix, input filename, output folder, and an optional data root (default empty; this feature never supplies one).

Plot function (plot_2d_or_3d_image, monai/visualize/img2tensorboard.py):
- Parameters in order: data (tensor or array in NCHW[D] layout; one item is plotted), step, writer, index (0), max channels (1), max frames (64), tag ('output'). Accepts a tensor or numpy array. Returns nothing.

ClassificationSaver completion hook:
- On the engine's completion event, the handler registers a callable that accepts and ignores the engine argument, then calls the CSV saver's finalize with no arguments.

TensorBoard image handler (TensorBoardImageHandler, monai/handlers/tensorboard_handlers.py):
- Constructor: summary writer (optional; a new writer is created if none), batch transform, output transform, global iteration transform, index (0), max channels (1), max frames (64). The index parameter is new and sits before max channels.
- Callable with the engine; per-call behavior is as in Workflows.

Segmentation saver handler (SegmentationSaver, monai/handlers/segmentation_saver.py):
- Constructor: output directory (current directory), output postfix ('seg'), output extension ('.nii.gz'), dtype (none), batch transform (identity), output transform (identity), name (optional). Output directory replaces the former output path parameter.
- attach: sets the logger if none is set, from name or the engine's logger. Registers the per-iteration hook if not already registered.
- Call: gets meta data and output, calls the NIfTI saver's batch save once, then logs. It holds one NIfTI saver built from output directory, postfix, extension, and dtype.

Classification saver handler (ClassificationSaver, monai/handlers/classification_saver.py):
- Constructor: output directory (current directory), filename ('predictions.csv'), overwrite (true), batch transform, output transform, name. The filename parameter is new and sits before overwrite.
- attach: sets the logger as above, registers the per-iteration hook and the completion hook. Attach must complete without error on the pinned ignite version.
- Call: gets meta data and output, and calls the CSV saver's batch save once.

## Module architecture
- monai/data/csv_saver.py and monai/data/nifti_saver.py (new) use the standard library, numpy, torch, and the NIfTI writer as needed. No ignite.
- monai/visualize/img2tensorboard.py: the plot function sits beside the existing animated-GIF helpers and uses the rescale helper in monai/transforms/utils.
- Segmentation and classification handler modules keep their ignite imports, hold a saver instance, and delegate, with no file-writing loops or file-name construction.
- Batch iteration belongs to the savers. Handlers depend on data and visualize; data and visualize never import handlers or ignite.

## Implementation constraints
- Savers and the plot function take no engine object. Their inputs are plain data, paths, and a SummaryWriter.
- The pinned ignite version (pytorch-ignite 0.3.0) rejects a completion handler without an engine argument at attach time. The classification handler therefore registers an engine-accepting wrapper around finalize; finalize itself keeps taking no engine argument.
- Convert tensors to numpy (detach, move to CPU) before any numpy operation, including inside the plot function. The rescale helper requires numpy input.
- Write NIfTI files only through the existing NIfTI writer. The plot function must not construct its own SummaryWriter.
- Leave the existing animated-GIF helpers unchanged. Add no new dependencies, requirements, or setup-file changes.

## Validation
- CSV filename: a string ending in '.csv', checked by assertion. Plot function: the writer must be a SummaryWriter, checked by assertion.
- TensorBoard handler: after tensor conversion, each non-None input, label, and output must be an array; otherwise raise ValueError with the original handler's wording for each of the three messages.

## Error handling
- A missing filename_or_obj key in meta data propagates as KeyError. Do not wrap it or convert it to ValueError.
- Absent meta data falls back to the item index without raising.

## Logging
- The segmentation handler logs one info message after each batch save, with the text 'saved all the model outputs as nifti files.'.
- The handler logger is a plain assignable attribute, set in attach to the engine's logger when none is set, or from the name argument. The savers and the classification handler do not log.

## Documentation
- Use Google-style docstrings with Args blocks. The segmentation handler's call docstring keeps the sentence that the output file datatype is determined from the engine output dtype.
- Saver docstrings describe the meta data keys and the item-index fallback. The CSV saver's overwrite docstring states that when overwrite is false, rows loaded from an existing file replace in-memory values with the same key.

## Maintainability
- All new and changed files, including tests and examples, must pass the root flake8 configuration, including the E-series checks. Put a space after every comma in call arguments and list literals.
- Each new and changed file ends with exactly one line break after its last code line, with no blank line after it (the CI lint job fails on W391).

## Compatibility
- Intended breaking changes: SegmentationSaver renames the output path parameter to output_dir, takes positional order output directory, postfix, extension, dtype, transforms, name, and changes the default dtype from the string float32 to none. ClassificationSaver inserts filename before overwrite. TensorBoardImageHandler inserts index before max channels.
- Handler attributes such as output_path need not be retained, and no output_path alias is required. The default file layout and CSV contents are unchanged.

## Behavioral acceptance criteria
- CSV: save_batch of eight zero values named testfile0 through testfile7, then finalize, writes predictions.csv with eight rows in order, each starting with its name.
- NIfTI: save_batch of zeros with shape eight by one by two by two, named testfile0 through testfile7, creates output/testfileN/testfileN_seg.nii.gz for each N. Input 'sub/case0.nii.gz' produces output/case0/case0_seg.nii.gz. Without meta data, or with empty meta data, items are named by index.
- Dtype: a NIfTI saver with no dtype writes the data's own dtype; with a dtype set, it writes that dtype. The segmentation handler's default keeps an integer output as an integer.
- Segmentation handler: attaches to an ignite engine and writes files with the layout above, using the output_dir keyword.
- Classification handler: attaches on the pinned version without error, accepts filename, and writes predictions.csv when the engine completes.
- Plot: torch zero tensors with shapes (1,1,10,10), (1,3,10,10), (1,4,10,10), (1,1,10,10,10), and (1,3,10,10,10) each plot without error and create the run output. A three-dimensional non-RGB item writes exactly one image, for channel 0, with suffix HW_0; with max channels 0, none is written.
- TensorBoard handler: index selects which batch element is plotted.
- Keyword calls: save_batch with batch_data and save with data succeed on both the CSV and NIfTI savers.

## Test requirements
- Test files: tests/test_csv_saver.py, tests/test_nifti_saver.py, tests/test_handler_segmentation_saver.py, tests/test_handler_classification_saver.py (updated), and tests/test_plot_2d_or_3d_image.py. Each uses unittest, parameterized shape cases, temporary directories removed after each test, and repository test naming.
- Expected paths match the layout rules under Data model. Tests check that output exists rather than pixel values for constant input.
- Plot tests for three-dimensional single-channel input assert the tag followed by '_HW_0' (for example input_0_HW_0). The overwrite-false CSV test asserts that file values replace in-memory values for shared keys and that row order follows the merge rule.
- The updated classification handler test passes filename. The integration sliding-window test uses output_dir.
