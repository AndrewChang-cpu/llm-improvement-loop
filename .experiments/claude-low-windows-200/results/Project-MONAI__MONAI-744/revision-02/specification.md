# Generalized Wasserstein Dice Loss

## Goals
- Add a segmentation loss class, GeneralizedWassersteinDiceLoss, to MONAI's losses package. It computes a Dice-type overlap score in which each voxel's true-positive contribution is discounted by a Wasserstein distance between the predicted class distribution and the ground-truth label, using a class-distance matrix. Per-class weights follow the generalized Dice weighting (inverse volume).
- The loss is used the way existing segmentation losses are used: raw logits in, integer class-index label maps as targets, a scalar loss out.
- The class is exported from the losses package, and a lowercase alias is defined in the dice module.

## Scope
In scope:
- One new class in the dice module, placed after the existing generalized Dice class.
- Two additional imports in the dice module (numpy and the torch functional module).
- The package export of the class in the losses package initializer.
- A lowercase module-level alias in the dice module.
- One new unit test module.

Out of scope:
- Any change to existing loss classes, their constructors, or their forward methods.
- Any change to the LossReduction enum or to shared utilities.
- Weight-type, masking, sigmoid, softmax, or one-hot option flags on the new class.
- Edits to the Sphinx documentation pages under docs/source. Docstrings inside the code are in scope (see Documentation).
- New third-party packages.

## Assumptions
- Input is a floating-point tensor of logits with shape batch, classes, then zero or more spatial dimensions (2D or 3D).
- Target is an integer tensor of class indices with shape batch, spatial dimensions, or shape batch, 1, spatial dimensions. Both forms are accepted.
- The distance matrix is square, with size C by C, where C equals the number of input channels. Its entries are nonnegative. It is supplied as a 2D torch tensor or a 2D numpy array.
- Label values lie in the range 0 to C minus 1. The reference does not check this.

## Terminology
- Logits: raw network outputs. Softmax over the class dimension converts them to probabilities.
- Distance matrix M: the C by C class-distance matrix, stored after optional max normalization.
- Wasserstein distance map W(v): for voxel v with ground-truth label y(v), W(v) equals the sum over classes k of M[y(v), k] times p_k(v), where p_k(v) is the softmax probability of class k at voxel v.
- Volume V(b, c): the number of voxels in sample b whose label is c.
- Class weight alpha(b, c): 1 divided by (V(b, c) + 1). A class absent from a sample has weight 1.
- Generalized true positives TP_b: the sum over voxels v of alpha(b, y(v)) times (1 minus W(v)).
- Denominator D_b: the sum over voxels v of alpha(b, y(v)) times (2 minus W(v)).

## Workflows
Construction:
1. Check that the distance matrix is square. If it is not, raise an error (see Error handling).
2. If the matrix is a numpy array, convert it to a torch tensor. Keep the tensor from this point on.
3. If the maximum entry of the matrix is not exactly 1, divide the whole matrix by its maximum. If the maximum is already 1, leave it unchanged.
4. Store the normalized matrix and the number of classes (the matrix size).
5. Pass the reduction setting to the parent loss initializer through the shared LossReduction conversion, so that the stored value is the enum's string value. Invalid reduction values fail there.

Forward (arguments: input, target, and smooth with default 1e-5):
1. Flatten the input to batch by classes by N, where N is the product of the spatial sizes. Flatten the target to batch by N, accepting both the batch-spatial and batch-1-spatial shapes.
2. Apply softmax over the class dimension of the flattened input to obtain probabilities. The input is always treated as logits; no flag changes this.
3. Compute the Wasserstein distance map W for every voxel using the stored matrix, moved to the probabilities' device at call time.
4. Compute the class weights alpha from the label counts per sample and class. Classes with zero voxels receive weight 1, not a large sentinel value.
5. Compute TP_b and D_b as defined in Terminology.
6. For each sample, compute the score (2 times TP_b plus smooth) divided by (D_b plus smooth), and the per-sample loss as 1 minus that score.
7. Return the mean of the per-sample losses over the batch as a scalar tensor. The reduction setting is stored but is not applied inside forward.

Helpers: the four helper methods in API contracts carry out steps 3 to 5. forward calls them. Their outputs are per-voxel values or per-sample values as described above.

## Data model
- Stored state on the loss object: the normalized distance matrix (C by C, the same tensor type as after numpy conversion), the number of classes C, and the reduction string.
- Input: float logits of shape batch, classes, spatial dimensions.
- Target: integer class-index labels of shape batch, spatial dimensions, or batch, 1, spatial dimensions. One-hot targets are not part of the contract.
- Output: one scalar tensor.

## API contracts
- The class is named GeneralizedWassersteinDiceLoss and inherits from the same torch loss base class used by the sibling loss classes.
- The constructor takes exactly two parameters, in this order:
  - The distance matrix, first, required, with no default. The keyword name is dist_matrix. It accepts a 2D torch tensor or a 2D numpy array.
  - The reduction, second, with default MEAN. It accepts a LossReduction member or its string value. It is passed to the parent initializer and stored. It does not change the value forward returns, so forward always returns the batch mean whatever reduction is given (see Documentation and Behavioral acceptance criteria).
- The constructor has no other parameters. Weight-type, include-background, to-one-hot, sigmoid, and softmax flags are not part of this class. Changing the position of reduction breaks callers.
- The forward method takes input, target, and a smooth argument with default 1e-5. smooth belongs to forward, not to the constructor, as in the sibling Generalized Dice loss.
- forward returns a scalar tensor.
- The class exposes these public helper methods, each with the described role:
  - wasserstein_distance_map: takes flattened probabilities and flattened target; returns per-voxel distances.
  - compute_weights_generalized_true_positives: takes flattened target; returns per-sample, per-class alpha weights.
  - compute_generalized_true_positive: takes alpha, flattened target, and the distance map; returns per-sample TP.
  - compute_denominator: takes alpha, flattened target, and the distance map; returns per-sample D.
- The public attributes are the normalized matrix and the class count, named as in the reference (matrix and num_classes).
- The module-level name generalized_wasserstein_dice refers to the class. It is defined in the dice module only and is not added to the losses package exports.
- The losses package exports GeneralizedWassersteinDiceLoss.

## Module architecture
- Location: the dice module, after the generalized Dice class and before the module-level alias block.
- The class is self-contained. It does not call other loss classes or add module-level helper functions.
- Reuse the shared LossReduction enum from the monai utilities for the reduction setting.
- Package wiring: the losses package initializer imports the new class from the dice module next to the existing dice-module exports. Existing exported names are unchanged.

## Implementation constraints
- Use vectorized tensor operations over batch and voxels. Do not loop over voxels or samples in Python.
- Use the class index labels only as gather or indexing keys; they must be integer typed.
- Compute alpha from counts only, with no sentinel or large constant weights for empty classes.
- Do not add shape, dtype, or label-range validation inside forward. Index targets, batch-1-spatial targets, and logits must reach the computation unchanged.
- Do not add sigmoid, one-hot conversion, or weight-type options.
- Do not apply reduction inside forward; forward returns the batch mean. Do not reproduce the sibling classes' reduction branches inside forward.

## Dependencies
- The dice module newly imports numpy and the torch functional module. Both are already MONAI dependencies. No new package is introduced.
- Use torch's functional one-hot for label counting in the class.
- Use the existing LossReduction enum from monai utilities.

## Naming
- Class: GeneralizedWassersteinDiceLoss, CamelCase with a Loss suffix, matching sibling classes.
- Module alias: generalized_wasserstein_dice, lowercase, matching the generalized_dice alias pattern.
- Methods: the snake_case names listed in API contracts.
- Parameters: dist_matrix, reduction, smooth, input, target, and the helper parameter names used in the reference (alpha, flat_target, flat_proba, wasserstein_distance_map).

## Validation
- The constructor checks only that the matrix is square.
- Reduction is validated only through the shared LossReduction conversion.
- forward performs no dtype, device, shape, or label validation. Invalid inputs fail in the tensor operations.

## Error handling
- A non-square distance matrix raises ValueError with the message "Dist Matrix is invalid."
- An invalid reduction value raises the ValueError from the LossReduction conversion.
- Errors from tensor operations inside forward propagate unchanged. Do not wrap or pre-check them.

## Documentation
- The class docstring states the purpose and cites the two source papers: Fidon et al., Generalised Wasserstein Dice Score, MICCAI BrainLes 2017, and Sudre et al., Generalised Dice overlap, MICCAI DLMIA 2017. It notes that the weighting follows the generalized Dice loss.
- Each helper method has a short docstring with an Args section in the style of the sibling classes.
- The constructor docstring documents the distance matrix (square, tensor or numpy) and names the reduction as the reduction mode, with the ValueError for a non-square matrix listed under Raises.
- The constructor docstring must not list "none" or "sum" as reduction output modes, and must not describe a per-element or summed output. It must state that the returned loss is the batch mean regardless of reduction.
- Keep every added line within 120 columns.
- Do not edit docs/source/losses.rst. Existing autodoc entries, including the generalized_dice entry and its members option, must stay as they are.

## Performance
- Cost is proportional to batch times classes times voxels, with one class-by-class matrix gather per call. No per-voxel loops.
- The distance matrix is moved to the probability device on each forward call. Keep the stored matrix unchanged.

## Reliability
- smooth is added to the numerator and denominator to avoid division by zero.
- Softmax over the class dimension keeps probabilities in [0, 1] for any logits. With confident correct logits the loss approaches 0; with confident wrong logits it approaches 1.

## Maintainability
- Keep the four helper methods as separate steps, so each stage can be checked on its own.
- Keep the docstrings describing each stage's formula.

## Compatibility
- The change is additive. No existing class signature, export, or alias changes.
- The positional order of the constructor (distance matrix, then reduction) is a public contract.

## Operations
- No runtime configuration or environment variables.
- Output is on the same device as the input logits.

## Behavioral acceptance criteria
- Binary 2D case: a batch of one, a 4 by 4 target label map whose inner 2 by 2 block is label 1 and the rest is label 0. With a 2 by 2 distance matrix that is 0 on the diagonal and 1 off it, and logits equal to 1000 times the one-hot of the target (channels first), the loss is 0 to 3 decimal places. The same target with an added channel dimension gives the same result. Logits equal to 1000 times the one-hot of the flipped target give a loss of 1 to 3 decimal places.
- Empty class case: a 4 by 4 target that is all label 0 with two classes. Logits equal to 1000 times the one-hot of the target give a loss of 0 to 3 decimal places. Flipped logits give 1 to 3 decimal places.
- A numpy distance matrix and an equivalent tensor give the same loss.
- A distance matrix whose maximum is 2 (zero on the diagonal, 2 off it) gives the same loss as its max-normalized form.
- A non-square distance matrix raises ValueError at construction.
- The returned value is a scalar. Changing reduction (to mean, sum, or none) does not change the returned value.
- The constructor docstring does not list none or sum as reduction outputs and states that the loss is the batch mean.
- The module-level alias generalized_wasserstein_dice is the same object as the class.

## Test requirements
- Add tests/test_generalized_wasserstein_dice_loss.py, following the per-loss test convention of the sibling tests: the 2020 MONAI Consortium license header, unittest, a test class, and a main guard.
- The module has two tests: one for the binary 2D case and one for the empty class case, with the scenarios and tolerance (3 decimal places) given above.
- Targets in the tests are integer label maps, not one-hot tensors.
- Test helpers that build class-first one-hot predictions use the one-hot function followed by a dimension permutation, as the sibling tests do. Tests must not use tensor methods introduced after the repository's declared minimum torch version (torch 1.4).
- The tests exist in the patch. They are not required to be executed by the harness.
