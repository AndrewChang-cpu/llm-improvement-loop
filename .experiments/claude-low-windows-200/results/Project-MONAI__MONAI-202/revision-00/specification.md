201 refactor event handlers for flexibility

Fixes #201 .

### Description
This PR refactor the event handlers to split the code structure to 2 levels, then we can call the same functions even without ignite.
Implemented:
(1) save data as an image to TensorBoard.
(2) save segmentation model output as Nifti format image file.
(3) save classification model output as CSV file.
(4) unit tests for nifti_saver, csv_saver, plot_2d_or_3d_image, segmentation_saver.

### Status
**Ready**

### Types of changes
<!--- Put an `x` in all the boxes that apply, and remove the not applicable items -->
- [ ] Bug fix (non-breaking change which fixes an issue)
- [x] Breaking change (fix or new feature that would cause existing functionality to change)
- [x] New tests added to cover the changes
- [x] Docstrings/Documentation updated

