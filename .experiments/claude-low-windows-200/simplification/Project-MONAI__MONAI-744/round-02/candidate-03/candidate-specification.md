# Generalized Wasserstein Dice Loss

## Goals
- Add GeneralizedWassersteinDiceLoss to MONAI's losses package. It computes a Dice-type overlap score in which each voxel's true-positive contribution is discounted by a Wasserstein distance between the predicted class distribution and the ground-truth label, using a class-distance matrix. Class weights follow the generalized Dice weighting (inverse volume).
- Usage matches existing segmentation losses: raw logits in, integer class-index label maps as targets, a scalar loss out.
- Export the class from the losses package and define a lowercase alias in the dice module.

## Scope
In scope:
- One new class in the dice module, placed after the existing generalized Dice class.
- Two new imports in the dice module: numpy and the torch functional module.
- The package export in the losses package initializer.
- A lowercase module-level alias in the dice module.
- One new unit test module.

Out of scope:
- Any change to existing loss classes, the LossReduction enum, or shared utilities.
- Weight-type, masking, sigmoid, softmax, or one-hot option flags on the new class.
- Edits to docs/source. Code docstrings are in scope.
- New third-party packages.

## Assumptions
- Input is a floating-point logits tensor of shape batch, classes, then zero or more spatial dimensions. The spatial dimension count is unrestricted.
- Input and target both carry a leading batch axis, and batch sizes match. Unbatched label maps are outside the contract; do not accept, reshape, or work around them.
- Target is an integer tensor of class indices with shape batch, spatial dimensions, or batch, 1, spatial dimensions. Both forms are accepted.
- The distance matrix is square, C by C, where C is the number of input channels. Entries are nonnegative. It is a 2D torch tensor or a 2D numpy array.
- Label values lie in 0 to C minus 1. The reference does not check this.

## Terminology
- Distance matrix M: the C by C class-distance matrix, after optional max normalization.
- Wasserstein distance map W_s(v): for sample s and voxel v with ground-truth label y_s(v), the sum over classes k of M[y_s(v), k] times p_k,s(v), where p_k,s(v) is the softmax probability of class k at that voxel. W is computed for every sample in the batch.
- Volume V(b, c): the number of voxels in sample b whose label is c.
- Class weight alpha(b, c): 1 divided by (V(b, c) + 1). A class absent from a sample has weight 1.
- Generalized true positives TP_b: for each sample b, the sum over every sample index s in the batch and every voxel v of alpha(b, y_b(v)) times (1 minus W_s(v)). The weight uses sample b's own labels and volumes; the distance term comes from every sample s. This cross-sample coupling is the reference behavior and is intentional. A sum over each sample's own distance map alone is not acceptable. For a batch of one, s ranges over sample b only.
- Denominator D_b: the same sum with (2 minus W_s(v)) in place of (1 minus W_s(v)), with the same coupling.

## Workflows
Construction:
1. Pass the reduction setting to the parent loss initializer through the shared LossReduction conversion, so the stored value is the enum's string value. Invalid reduction values fail here, before the matrix check.
2. Check that the distance matrix is square.
3. Convert a numpy matrix to a torch tensor.
4. If the maximum entry is not exactly 1, divide the whole matrix by its maximum; otherwise leave it unchanged.
5. Store the normalized matrix as m and its size as num_classes.

Forward (input, target, smooth with default 1e-5):
1. Flatten the input to batch by classes by N, where N is the product of the spatial sizes. Flatten the target to batch by N, accepting both target shapes.
2. Apply softmax over the class dimension. The input is always treated as logits.
3. Compute W for every sample and voxel using the stored matrix, moved to the probabilities' device at call time. The result has shape batch by N.
4. Compute alpha from label counts per sample and class. Classes with zero voxels receive weight 1, not a sentinel value.
5. Compute TP_b and D_b for every sample b with the cross-sample rule: pair b's per-voxel alpha map with the distance maps of all samples s, form the product with (1 minus W) for TP or (2 minus W) for D over the (b, s, voxel) combinations, and sum over the s and voxel axes. This gives one value per sample b.
6. For each sample b, compute the score (2 times TP_b plus smooth) divided by (D_b plus smooth). The per-sample loss is 1 minus that score.
7. Return the mean of the per-sample losses as a scalar tensor. Reduction is stored but not applied inside forward.

The four helper methods in API contracts carry out steps 3 to 5, and forward calls them.

## Data model
- Stored state: the normalized matrix m (C by C torch tensor), num_classes, and the reduction string.
- Input: float logits of shape batch, classes, spatial dimensions.
- Target: integer class-index labels of shape batch, spatial dimensions, or batch, 1, spatial dimensions. One-hot targets are not part of the contract.
- Output: one scalar tensor.

## API contracts
- The class is named GeneralizedWassersteinDiceLoss and inherits from the same torch loss base class as the sibling loss classes.
- Constructor takes exactly two parameters, in this order:
  - dist_matrix, first, required. Accepts a 2D torch tensor or a 2D numpy array.
  - reduction, second, default MEAN. Accepts a LossReduction member or its string value. It is passed to the parent and stored, but does not change forward's return value, which is always the batch mean.
- No other constructor parameters. Weight-type, include-background, to-one-hot, sigmoid, and softmax flags are not part of this class. Changing the position of reduction breaks callers.
- forward takes input, target, and smooth with default 1e-5, as in the sibling Generalized Dice loss. It returns a scalar tensor.
- Public helper methods (pseudocode-level descriptions, not code):
  - wasserstein_distance_map: takes flattened probabilities (batch by classes by N) and flattened target (batch by N); returns per-voxel distances for every sample (batch by N).
  - compute_weights_generalized_true_positives: takes flattened target; returns alpha weights (batch by classes).
  - compute_generalized_true_positive: takes alpha, flattened target, and the full batch distance map (batch by N); returns one TP value per sample (shape batch), using the cross-sample rule.
  - compute_denominator: takes alpha, flattened target, and the full batch distance map (batch by N); returns one D value per sample (shape batch), using the cross-sample rule.
- Instance attributes: m and num_classes.
- The module-level name generalized_wasserstein_dice refers to the class. It is defined in the dice module only, not added to the losses package exports.
- The losses package exports GeneralizedWassersteinDiceLoss.

## Module architecture
- Location: the dice module, after the generalized Dice class and before the module-level alias block.
- The class is self-contained. It does not call other loss classes or add module-level helper functions.
- Use the shared LossReduction enum from monai utilities.
- Package wiring: the losses package initializer imports the new class from the dice module next to the existing dice exports. Existing exported names are unchanged.

## Implementation constraints
- Use vectorized tensor operations over batch and voxels. No Python loops over voxels or samples.
- Labels are used only as integer gather or indexing keys.
- Compute alpha from counts only, with no sentinel or large constant weights for empty classes.
- No shape, dtype, device, or label-range validation inside forward. Targets, batch-1-spatial targets, and logits reach the computation unchanged.
- No sigmoid, one-hot conversion, or weight-type options.
- No reduction inside forward. Do not reproduce the sibling classes' reduction branches.
- The TP and D helpers must couple samples as described in Terminology.

## Dependencies
- The dice module newly imports numpy and the torch functional module. Both are existing MONAI dependencies.
- Use torch's functional one-hot for label counting.

## Naming
- Class: GeneralizedWassersteinDiceLoss. Module alias: generalized_wasserstein_dice, matching the generalized_dice alias pattern.
- Methods: the snake_case names in API contracts. Attributes: m and num_classes.
- Parameters: dist_matrix, reduction, smooth, input, target, and the reference's helper parameter names (alpha, flat_target, flat_proba, wasserstein_distance_map).

## Validation and error handling
- The constructor checks only that the matrix is square. A non-square matrix raises ValueError with the message "Dist Matrix is invalid."
- Reduction is validated only through the shared LossReduction conversion; an invalid value raises that conversion's ValueError.
- forward performs no dtype, device, shape, or label validation. Errors from tensor operations propagate unchanged.

## Documentation
- The class docstring states the purpose, cites Fidon et al., Generalised Wasserstein Dice Score, MICCAI BrainLes 2017, and Sudre et al., Generalised Dice overlap, MICCAI DLMIA 2017, and notes that the weighting follows the generalized Dice loss.
- Each helper has a short docstring with an Args section in the style of the sibling classes. The docstrings of compute_generalized_true_positive and compute_denominator state that the sum runs over every sample's distance map in the batch, so each value depends on the whole batch.
- The constructor docstring documents the distance matrix (square, tensor or numpy), names reduction as the reduction mode, lists the ValueError under Raises, and states that the returned loss is the batch mean regardless of reduction. It must not list "none" or "sum" as output modes.
- Keep added lines within 120 columns.
- Do not edit docs/source/losses.rst. Existing autodoc entries stay as they are.

## Performance and reliability
- Cost is proportional to batch times batch times voxels for the cross-sample TP and D terms, plus batch times classes times voxels for the other steps.
- Gather-style indexing in three places: the distance helper picks each voxel's distance row by its label; the TP and D helpers pick each voxel's alpha by its label.
- Move the distance matrix to the probability device on each forward call; keep the stored matrix unchanged.
- smooth is added to numerator and denominator to avoid division by zero.
- Softmax keeps probabilities in [0, 1]. The loss approaches 0 when every sample is confidently correct and 1 when every sample is confidently wrong.
- Output is on the same device as the input logits. No runtime configuration or environment variables.

## Maintainability
- Keep the four helper methods as separate steps so each stage can be checked on its own.
- Keep docstrings describing each stage's formula, including the batch-wide sum for TP and D.
- The change is additive. No existing class signature, export, or alias changes, and the constructor's positional order is a public contract.

## Behavioral acceptance criteria
- Binary 2D case: batch of one, 4 by 4 target with inner 2 by 2 block labeled 1 and the rest 0, shape batch 1, 4, 4. With a 2 by 2 distance matrix that is 0 on the diagonal and 1 off it, and logits equal to 1000 times the one-hot of the target with the class axis at channel position 1 (logit shape batch 1, classes 2, 4, 4), the loss is 0 to 3 decimal places. The same target with an added size-1 channel dimension (shape batch 1, 1, 4, 4) gives the same result. Logits equal to 1000 times the one-hot of the flipped target give a loss of 1 to 3 decimal places.
- Empty class case: 4 by 4 target all label 0, two classes, batch axis of size 1. Logits equal to 1000 times the one-hot of the target, class axis at channel position 1, give a loss of 0 to 3 decimal places. Flipped logits give 1 to 3 decimal places.
- Batch-coupling case (batch of two): same 2 by 2 distance matrix; sample 0 is an all-zero 2 by 2 target and sample 1 is an all-one 2 by 2 target. Logits for both samples are 1000 times the one-hot of class 0 at every voxel (sample 0 correct, sample 1 wrong). The expected loss is approximately 0.333 to 3 decimal places. Each sample's TP is 0.8 and D is 2.4 under the cross-sample rule. A per-sample-only computation gives 0.5 and fails this criterion.
- A numpy distance matrix and an equivalent tensor give the same loss.
- A distance matrix whose maximum is 2 (zero on the diagonal, 2 off it) gives the same loss as its max-normalized form.
- A non-square distance matrix raises ValueError at construction.
- The returned value is a scalar, and changing reduction (mean, sum, or none) does not change it.
- The module-level alias generalized_wasserstein_dice is the same object as the class.

## Test requirements
- Add tests/test_generalized_wasserstein_dice_loss.py, following the sibling per-loss test convention: 2020 MONAI Consortium license header, unittest, a test class, and a main guard.
- Two tests: the binary 2D case and the empty class case, with the scenarios and 3-decimal tolerance above.
- Targets are integer label maps, not one-hot tensors. Every label map, including those used to build predictions, carries a leading batch axis (size 1) before any one-hot step. Do not pass an unbatched two-dimensional label map to the loss or a test helper.
- Prediction helpers follow the reference test order: take the batched integer label map, one-hot encode with the number of classes, move the class axis (currently last) to channel position 1, then scale by 1000 and cast to float. The result has channel count equal to the number of classes (2). Verify this by reading the helper and its calls before finishing.
- For the optional class-dimension target variant, insert a size-1 axis after the batch axis. Do not change the prediction layout for that case.
- Tests must not use tensor methods introduced after the minimum supported torch version (1.4).
- The tests are part of the patch; the harness does not require them to be executed.
