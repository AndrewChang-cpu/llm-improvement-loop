## Goals
- Make the feature's file-writing and image-plotting logic usable without an ignite engine. Provide an engine-free CSV saver and an engine-free NIfTI saver in the data package, and an engine-free 2D/3D image plotting function in the visualization package.
- Keep the three ignite-facing components (segmentation saver handler, classification saver handler, TensorBoard image handler) as thin adapters. Each reads engine state through its transforms, then delegates to a saver or the plotting function in a single call.
- Support single-item and batch saving on the savers, with optional metadata-driven naming, and expose the constructor options listed under API contracts.
- Keep the file outputs that the reference defines, including the dtype rule for NIfTI output.

## Scope
In scope:
- New module monai/data/csv_saver.py holding the CSV saver.
- New module monai/data/nifti_saver.py holding the NIfTI saver.
- A new plotting function added to the existing module monai/visualize/img2tensorboard.py.
- Changes to monai/handlers/segmentation_saver.py, monai/handlers/classification_saver.py, and monai/handlers/tensorboard_handlers.py.
- Changing the default dtype argument of the NIfTI writer in monai/data/nifti_writer.py from the string form to the numpy float32 type. This is the same value and is not a behavior change.
- Updating in-repo callers of the renamed parameter: examples/segmentation_3d/unet_evaluation_array.py, examples/segmentation_3d/unet_evaluation_dict.py, and tests/integration_sliding_window.py.
- The tests listed under Test requirements.
Out of scope:
- Changes to the transforms package, other handlers, or the ignite attach and event-registration mechanics beyond what is described here.
- New package dependencies, and any new module beyond the two data modules. Documentation pages are optional.

## Terminology
- Item: one entry along the first (batch) dimension of a data array or tensor. The data of one item is channel-first (channels, then spatial dimensions).
- Batch: data whose first dimension indexes items. The save_batch operations iterate over it.
- Meta data mapping: a mapping whose keys hold per-item values. The keys used are filename_or_obj, affine, and original_affine. In batch calls each value is a per-item sequence, indexed in parallel with the batch.
- Item index: a running counter, starting at zero, kept by each saver. It increments on every single-item save, including each item within a batch. It is used as the name only when no meta data is given.
- Ignite-free: the module imports neither ignite nor the monai handlers package, and does not take an engine object.
- Data root: an optional root directory used to preserve relative folder structure. This feature never supplies one, so it is treated as empty.

## Workflows
1. Classification (CSV) through the handler: when each iteration completes, the classification handler gets meta data from its batch transform, gets model output from its output transform, and calls the CSV saver's batch save once with both. On the completion event, the handler calls the saver's finalize, which writes the CSV file. The handler does not loop over items itself.
2. Segmentation (NIfTI) through the handler: when each iteration completes, the segmentation handler gets meta data and output the same way and calls the NIfTI saver's batch save once. It then logs one info message.
3. Standalone use without ignite: a caller constructs the CSV or NIfTI saver directly and calls single-item save or batch save. The NIfTI saver writes each item immediately. The CSV saver writes its file only when finalize is called.
4. TensorBoard image handler: on each call, compute the step from the global iteration transform. Then, for three sources in this order, skip the source if it is None; otherwise convert a tensor to numpy, require an array, and plot with the handler's index, max channels, and max frames:
   - the first element of the batch transform output, tag 'input_0';
   - the second element of the batch transform output, tag 'input_1';
   - the output transform result, tag 'output'.
   Flush the writer at the end.
5. Plot function:
   - Assert that the writer is a SummaryWriter.
   - Select the item at the index.
   - Convert a tensor to numpy.
   - Branch on the dimensionality of the selected item:
     - Two dimensions: rescale values to 0 to 1 and write one image with the tag suffix 'HW'.
     - Three dimensions: if the first dimension is 3 and max channels is 3, write one RGB image with the suffix 'CHW'. Otherwise write only the first channel, rescaled to 0 to 1, with the suffix 'HW_0'. Write nothing else.
     - Four or more dimensions: flatten the leading dimensions into a list of 3D volumes. For each of the first max-channels volumes, rescale to 0 to 255 and write one animated GIF with the suffix 'HWD_j', where j is the volume index. Use max frames as the frame count and a scale of 1.0, at the given step.
     - Any other dimensionality: write nothing and raise no error.

## Data model
CSV cache:
- The CSV saver holds an insertion-ordered mapping from a string key to a float32 array of values. A key is the filename_or_obj value when meta data is given, otherwise the string form of the item index.
- Saving with an existing key replaces its values and keeps the key's original position.
- Finalize writes one line per key, in insertion order. Each line is the key, then for each flattened value a comma followed by the value's text, then a newline. There is no header row.
- With overwrite false and an existing file, finalize first reads each existing row: the first column is the key and the remaining columns are parsed as float32. These rows are stored into the cache, replacing any in-memory values with the same key. Then the merged cache is written.
- Finalize creates the output directory if it is missing.

NIfTI output layout and dtype:
- For each input filename, remove the directory part and repeatedly strip extensions until none remain, to get a base name. The output path is the output directory, then the base name as a folder, then the base name joined with an underscore and the output postfix, then the output extension. The input's directory part is not preserved, because no data root is supplied.
- Without meta data, the item index string is used as the base name.
- Before writing, move the channel axis of each item to the last position. Write using the affine from meta data and the original affine from meta data, both optional and absent when not given.
- The written dtype is the saver's dtype when it is set, otherwise the data's own dtype. The default is none for the NIfTI saver and the segmentation handler. This keeps the model output dtype by default.

## API contracts
CSV saver (class CSVSaver in monai/data/csv_saver.py):
- Constructor parameters, in order: output directory (default the current directory), filename (default 'predictions.csv'), overwrite (default true). The filename must be a string whose last four characters are '.csv'. The file path is the output directory joined with the filename.
- save: takes one item and an optional meta data mapping (default none). With meta data, the key comes from filename_or_obj. Without it, the key is the string form of the item index. A tensor is detached, moved to CPU, and converted to numpy. Values are stored as float32. The item index advances by one.
- save_batch: takes a batch and an optional meta data mapping (default none). For each item along the first dimension, it calls save with that item. When meta data is given, the per-item mapping holds each key's value at the item's position. When it is none, each item uses none.
- finalize: takes no required argument. It writes the file as described under Data model.
- No engine parameter.

NIfTI saver (class NiftiSaver in monai/data/nifti_saver.py):
- Constructor parameters, in order: output directory (default the current directory), output postfix (default 'seg'), output extension (default '.nii.gz'), dtype (default none, meaning keep the data's dtype).
- save: takes one item and an optional meta data mapping (default none), with the naming, affine, and dtype rules above. It writes through the existing NIfTI writer function in monai/data/nifti_writer.py.
- save_batch: takes a batch and an optional meta data mapping (default none), with the same per-item rules as the CSV saver.
- The file-name helper is a private static method with the parameters postfix, input filename, output folder, and an optional data root (default empty).

Plot function (monai/visualize/img2tensorboard.py, function name plot_2d_or_3d_image):
- Parameters, in order: data (tensor or array in NCHW[D] layout; one item is plotted), step, writer, index (default 0), max channels (default 1), max frames (default 64), tag (default 'output').
- Accepts a tensor or a numpy array. Returns nothing.

TensorBoard image handler (class TensorBoardImageHandler in monai/handlers/tensorboard_handlers.py):
- Constructor parameters, in order: summary writer (optional; a new writer is created if none), batch transform, output transform, global iteration transform, index (default 0), max channels (default 1), max frames (default 64). The index parameter is new and sits before max channels.
- Per-call behavior is as in Workflows. The index is passed to the plot function for all three sources.
- It is callable with the engine. Plotting is delegated to the plot function, not implemented in the handler.

Segmentation saver handler (class SegmentationSaver in monai/handlers/segmentation_saver.py):
- Constructor parameters, in order: output directory (default the current directory), output postfix (default 'seg'), output extension (default '.nii.gz'), dtype (default none), batch transform (default identity), output transform (default identity), name (optional). The former output path parameter is replaced by the output directory parameter.
- attach: sets the logger if none is set, from name or from the engine's logger. Registers the per-iteration hook if it is not already registered.
- Call: gets meta data and output, calls the NIfTI saver's batch save once, then logs.
- Holds one NIfTI saver created from the output directory, postfix, extension, and dtype.

Classification saver handler (class ClassificationSaver in monai/handlers/classification_saver.py):
- Constructor parameters, in order: output directory (default the current directory), filename (default 'predictions.csv'), overwrite (default true), batch transform, output transform, name. The filename parameter is new and sits before overwrite.
- attach: sets the logger as above, registers the per-iteration hook, and registers a completion hook that calls the CSV saver's finalize.
- Call: gets meta data and output, and calls the CSV saver's batch save once.

## Module architecture
- monai/data/csv_saver.py (new): CSV saver only. Imports standard-library file and csv modules, numpy, and torch. No ignite and no monai handlers import.
- monai/data/nifti_saver.py (new): NIfTI saver. Imports numpy, torch, and the NIfTI writer in monai/data. No ignite.
- monai/visualize/img2tensorboard.py: holds the plot function next to the existing animated-GIF helpers. It uses the existing rescale helper in monai/transforms/utils. No new visualize module is created.
- monai/handlers/segmentation_saver.py and classification_saver.py: keep the ignite imports. They hold a saver instance and delegate. They contain no file-writing loops and no file-name construction.
- monai/handlers/tensorboard_handlers.py: imports the plot function from monai/visualize/img2tensorboard and calls it directly.
- Batch iteration belongs to the savers' batch operations. Handlers make one delegating call.
- Dependency layering: handlers depend on data and visualize. Data and visualize do not import handlers or ignite.

## Implementation constraints
- Savers and the plot function take no engine object. Their inputs are plain data, paths, and a SummaryWriter.
- Convert tensors to numpy (detach, move to CPU) before any numpy operation, including inside the plot function, so tensor input works for direct calls. The rescale helper requires numpy input.
- Write NIfTI files only through the existing NIfTI writer.
- The plot function must not construct its own SummaryWriter.
- Leave the existing animated-GIF helpers unchanged.
- Add no new dependencies.

## Dependencies
- Allowed: numpy, torch, the standard-library csv and os modules, the NIfTI writer in monai/data, the rescale helper in monai/transforms/utils, the existing tensorboard SummaryWriter, and ignite inside handler modules only.
- No new packages and no requirements or setup-file changes.
- Tests may use parameterized and the existing ignite engine.

## Naming
- The output directory parameter is named output_dir in the CSV saver, the NIfTI saver, the segmentation handler, and the classification handler. The name output_path is not used.
- CSV parameter: filename. NIfTI parameters: output postfix, output extension, dtype.
- The NIfTI file-name helper is private (leading underscore) and static.
- TensorBoard tags: input_0, input_1, output. Plot suffixes: HW, CHW, HW_j, HWD_j.
- Test files: tests/test_csv_saver.py, tests/test_nifti_saver.py, tests/test_handler_segmentation_saver.py, tests/test_handler_classification_saver.py (updated), tests/test_plot_2d_or_3d_image.py. Handler tests use the test_handler_ prefix.

## Validation
- CSV filename: must be a string ending in '.csv'. Checked by assertion.
- Plot function: the writer must be a SummaryWriter. Checked by assertion.
- TensorBoard handler: after tensor conversion, each non-None input, label, and output must be an array. Otherwise raise ValueError, using the original handler's wording for each of the three messages.
- Add no further validation (no checks on meta keys or data shape).

## Error handling
- A missing filename_or_obj key in meta data: let the natural key lookup failure propagate as KeyError. Do not wrap it or convert it to ValueError.
- Meta data of none: fall back to the item index. Raise nothing.
- Plot with an unsupported dimensionality: write nothing and raise nothing.
- Non-array values in the TensorBoard handler: raise ValueError as in Validation.

## Logging
- The segmentation handler logs one info message after each batch save, with the text 'saved all the model outputs as nifti files.'.
- Handler logger: a plain assignable attribute, not a computed property. Set in attach to the engine's logger when none is set, or from the name argument.
- The savers and the classification handler do not log.

## Documentation
- Use Google-style docstrings with Args blocks, following the repository convention.
- The segmentation handler's call docstring keeps the sentence that the output file datatype is determined from the engine output dtype.
- Saver docstrings describe the meta data keys and the none fallback to the item index.
- Docstrings must not cite export paths that the package does not provide. Classes are referenced by their module.
- Documentation pages are optional.

## Compatibility
- Intended breaking changes, per the reference:
  - SegmentationSaver: the output path parameter is renamed to output_dir. The positional order becomes output directory, postfix, extension, dtype, transforms, name. The default dtype changes from the string float32 to none.
  - ClassificationSaver: a filename parameter is inserted before overwrite.
  - TensorBoardImageHandler: an index parameter is inserted before max channels.
  - The handler attributes output_dir, overwrite, output_path, output_postfix, output_ext, and dtype need not be retained.
- In-repo callers are updated: examples/segmentation_3d/unet_evaluation_array.py, examples/segmentation_3d/unet_evaluation_dict.py, and tests/integration_sliding_window.py use output_dir. No output_path alias is required.
- The default dtype of none keeps the model output dtype, matching the original behavior, which ignored the dtype argument.
- The default file layout and the CSV contents for the default path are unchanged.

## Behavioral acceptance criteria
- CSV: save_batch of eight zero values with names testfile0 through testfile7, then finalize, writes predictions.csv with eight rows in order. Each row starts with its name, and the values are 0.
- NIfTI: save_batch of zeros with shape eight by one by two by two, with names testfile0 through testfile7, creates output/testfileN/testfileN_seg.nii.gz for each N.
- NIfTI without meta data: items are named by their index.
- NIfTI path layout: input 'sub/case0.nii.gz' produces output/case0/case0_seg.nii.gz. The directory part is dropped.
- Dtype: a NIfTI saver with no dtype writes the data's own dtype. With a dtype set, it writes that dtype. The segmentation handler's default keeps an integer output as an integer.
- Segmentation handler: attaches to an ignite engine and writes files with the layout above, using the output_dir keyword.
- Classification handler: accepts filename and writes predictions.csv with the rows.
- CSV with overwrite false: rows already in the file are retained, and file values replace in-memory values with the same key.
- Plot: torch zero tensors with shapes (1,1,10,10), (1,3,10,10), (1,4,10,10), (1,1,10,10,10), and (1,3,10,10,10) each plot without error and create the run output. Tensor input is accepted.
- Plot, three-dimensional non-RGB item: exactly one image is written, for channel 0.
- TensorBoard handler: the index selects which batch element is plotted.

## Test requirements
- Each of the five test files listed under Naming exists and follows the repository style: unittest, parameterized for shape cases, and temporary directories removed after each test.
- Expected paths must match the layout rules under Data model. Tests must not assert specific pixel values for constant input; they check that output exists.
- The updated classification handler test passes filename.
- The integration sliding-window test uses output_dir.
- Tests describe behavior and are not claimed to pass unless executed.
