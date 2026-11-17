# Generalized Wasserstein Dice Loss

## Goals
- Add GeneralizedWassersteinDiceLoss to MONAI's losses package: a Dice-type overlap loss that discounts each voxel's true-positive contribution by a Wasserstein distance between predicted class probabilities and the ground-truth label, via a class-distance matrix. Class weights follow generalized Dice (inverse volume).
- Usage matches existing segmentation losses: raw logits in, integer class-index label maps as targets, scalar loss out.
- Export the class from the losses package and define a lowercase alias in the dice module.

## Scope
In scope:
- One new class in the dice module, placed after the generalized Dice class, plus its lowercase alias.
- New numpy and torch functional imports in the dice module.
- The package export in the losses package initializer.
- One new unit test module and docstrings for the new code.

Out of scope:
- Changes to existing loss classes, the LossReduction enum, or shared utilities.
- Weight-type, masking, sigmoid, softmax, or one-hot option flags. New third-party packages. Sphinx pages under docs/source.

## Assumptions
- Input is a floating-point logits tensor shaped batch, classes, then zero or more spatial dimensions.
- Input and target both carry a leading batch axis, with matching batch sizes. Unbatched label maps are outside the contract; do not accept, reshape, or work around them.
- Target is an integer class-index tensor shaped batch plus spatial dimensions, or batch, 1, spatial dimensions.
- The distance matrix is square, C by C, where C is the input channel count, with nonnegative entries. It is a 2D torch tensor or 2D numpy array.
- Label values lie in 0 to C minus 1. The reference does not check this.

## Terminology
- Distance matrix M: the C by C class-distance matrix after optional max normalization.
- Wasserstein distance map W_s(v): for sample s and voxel v with ground-truth label y_s(v), the sum over classes k of M[y_s(v), k] times p_k,s(v), the softmax probability of class k at that voxel.
- Volume V(b, c): the number of voxels in sample b whose label is c.
- Class weight alpha(b, c): 1 divided by (V(b, c) + 1). A class absent from a sample has weight 1.
- Generalized true positives TP_b: for each sample b, the sum over every sample index s in the batch and every voxel v of alpha(b, y_b(v)) times (1 minus W_s(v)). The weight uses sample b's own labels; the distance term comes from every sample s. For a batch of one, s ranges over sample b only.
- Denominator D_b: the same sum with (2 minus W_s(v)) in place of (1 minus W_s(v)), with the same coupling.

## Workflows
Construction:
1. Convert reduction through the shared LossReduction conversion and pass it to the parent loss initializer, so the stored value is the enum's string value. Invalid reduction values fail here, before the matrix check.
2. Check that the matrix is square.
3. If the matrix is a numpy array, convert it to a torch tensor.
4. If the maximum entry is not exactly 1, divide the whole matrix by its maximum.
5. Store the normalized matrix as m and its size as num_classes.

Forward (input, target, smooth with default 1e-5):
1. Flatten the input to batch by classes by N, where N is the product of the spatial sizes. Flatten the target to batch by N, accepting both target shapes.
2. Apply softmax over the class dimension. Input is always treated as logits.
3. Compute W for every sample and voxel using m, moved to the probabilities' device at call time. The result has shape batch by N.
4. Compute alpha from per-sample class counts. Classes with zero voxels receive weight 1, not a sentinel value.
5. Compute TP_b and D_b for each sample b with the cross-sample rule: multiply b's per-voxel alpha by (1 minus W) for TP or (2 minus W) for D, over every sample s and voxel, and sum.
6. For each sample b, compute (2 times TP_b plus smooth) divided by (D_b plus smooth). The per-sample loss is 1 minus that score.
7. Return the mean of the per-sample losses as a scalar tensor. The reduction setting is stored but not applied inside forward.

## Data model
- Stored state: the normalized matrix m (C by C torch tensor), num_classes, and the reduction string.
- Target: integer class-index labels shaped batch, spatial dimensions, or batch, 1, spatial dimensions. One-hot targets are not part of the contract.

## API contracts
- The class inherits from the same torch loss base class as the sibling loss classes.
- The constructor takes exactly two parameters, in this order:
  - dist_matrix, first, required. It accepts a 2D torch tensor or a 2D numpy array.
  - reduction, second, default MEAN. It accepts a LossReduction member or its string value. It is passed to the parent and stored, but forward's return value is always the batch mean.
- forward takes input, target, and smooth with default 1e-5, matching the sibling Generalized Dice loss. It returns a scalar tensor.
- Public helper methods, each one stage of forward that can be checked on its own:
  - wasserstein_distance_map: takes flattened probabilities (batch, classes, N) and flattened target (batch, N); returns per-voxel distances for every sample (batch, N).
  - compute_weights_generalized_true_positives: takes flattened target; returns per-sample, per-class alpha weights (batch, classes).
  - compute_generalized_true_positive: takes alpha, flattened target, and the full batch distance map (batch, N); returns one TP value per sample (shape batch), using the cross-sample rule.
  - compute_denominator: takes the same arguments as compute_generalized_true_positive; returns one D value per sample (shape batch), using the cross-sample rule.
- Instance attributes: m and num_classes.
- The module-level name generalized_wasserstein_dice refers to the class. It is defined in the dice module only and is not added to the losses package exports.
- The losses package exports GeneralizedWassersteinDiceLoss.

## Module architecture
- Location: the dice module, after the generalized Dice class and before the module-level alias block.
- The class is self-contained: it does not call other loss classes or add module-level helper functions.
- The losses package initializer imports the new class next to the existing dice-module exports. Existing exported names are unchanged.

## Implementation constraints
- Use vectorized tensor operations over batch and voxels. Do not loop over voxels or samples in Python.
- Use class-index labels only as gather or indexing keys; they must be integer typed.
- Compute alpha from counts only, with no sentinel or large constant weights for empty classes.
- Do not add shape, dtype, or label-range validation inside forward. Inputs reach the computation unchanged.
- Do not apply reduction inside forward, and do not reproduce the sibling classes' reduction branches.

## Dependencies
- The dice module newly imports numpy and the torch functional module. Both are existing MONAI dependencies.
- Use torch's functional one-hot for label counting.

## Naming
- Class: GeneralizedWassersteinDiceLoss. Module alias: generalized_wasserstein_dice, matching the generalized_dice pattern.
- Parameters: dist_matrix, reduction, smooth, input, target, and the reference helper parameter names (alpha, flat_target, flat_proba, wasserstein_distance_map).

## Validation
- The constructor checks only that the matrix is square. Reduction is validated only through the shared LossReduction conversion.
- forward performs no dtype, device, shape, or label validation.

## Error handling
- A non-square distance matrix raises ValueError with the message "Dist Matrix is invalid."
- An invalid reduction value raises the ValueError from the LossReduction conversion.
- Errors from tensor operations inside forward propagate unchanged.

## Documentation
- The class docstring states the purpose and cites Fidon et al., Generalised Wasserstein Dice Score, MICCAI BrainLes 2017, and Sudre et al., Generalised Dice overlap, MICCAI DLMIA 2017. It notes that the weighting follows the generalized Dice loss.
- Each helper has a short docstring with an Args section in sibling style. The docstrings of compute_generalized_true_positive and compute_denominator state that the sum runs over every sample's distance map, and each stage's docstring describes its formula.
- The constructor docstring documents the distance matrix (square, tensor or numpy), names reduction as the reduction mode, lists the ValueError under Raises, and states that the loss is the batch mean regardless of reduction. It must not list "none" or "sum" as output modes.
- Keep every added line within 120 columns.

## Performance
- Cost is proportional to batch times batch times voxels for the cross-sample TP and D terms, plus batch times classes times voxels for the other steps.
- Use gather-style indexing: the distance helper picks each voxel's distance row by its label; the TP and D helpers pick each voxel's alpha by its label. Move the matrix to the probability device on each forward call.

## Reliability
- smooth is added to the numerator and denominator to avoid division by zero.
- Softmax keeps probabilities in [0, 1]. The loss approaches 0 when every sample is confidently correct and 1 when every sample is confidently wrong.

## Compatibility
- The change is additive. No existing class signature, export, or alias changes. The constructor's positional order (distance matrix, then reduction) is a public contract.

## Operations
- No runtime configuration or environment variables. Output is on the same device as the input logits.

## Behavioral acceptance criteria
- Binary 2D case: a batch of one, with a 4 by 4 target whose inner 2 by 2 block is label 1 and the rest is label 0, shape batch 1, 4, 4. Use a 2 by 2 distance matrix that is 0 on the diagonal and 1 off it. Logits equal 1000 times the one-hot of the target, class axis at channel position 1 (shape batch 1, classes 2, 4, 4): the loss is 0 to 3 decimal places. The same target with an added size-1 channel dimension (shape batch 1, 1, 4, 4) gives the same result. Logits equal 1000 times the one-hot of the flipped target give a loss of 1 to 3 decimal places.
- Empty class case: a 4 by 4 all-zero target with two classes, batch size 1. Correct logits give a loss of 0 to 3 decimal places. Flipped logits give 1 to 3 decimal places.
- Batch-coupling case (batch of two): with the same distance matrix, sample 0 has an all-zero 2 by 2 target and sample 1 has an all-one 2 by 2 target. Logits for both samples are 1000 times the one-hot of class 0 at every voxel; sample 0 is correct and sample 1 is wrong. The expected loss is approximately 0.333 to 3 decimal places. Each sample's TP is 0.8 and D is 2.4 under the cross-sample rule. A per-sample-only computation gives 0.5 and fails this criterion.
- A numpy distance matrix and an equivalent tensor give the same loss.
- A distance matrix whose maximum is 2 (zero on the diagonal, 2 off it) gives the same loss as its max-normalized form.
- A non-square distance matrix raises ValueError at construction.
- The returned value is a scalar. Changing reduction (mean, sum, or none) does not change it.
- The module-level alias generalized_wasserstein_dice is the same object as the class.

## Test requirements
- Add tests/test_generalized_wasserstein_dice_loss.py, following the sibling per-loss test convention: 2020 MONAI Consortium license header, unittest, a test class, and a main guard. Tests are part of the patch; the harness does not require running them.
- The module has two tests: the binary 2D case and the empty class case, with the scenarios and 3-decimal tolerance above.
- Targets are integer label maps, not one-hot tensors. Every label map passed to the loss or used to build predictions has a leading batch axis (size 1) before any one-hot step. Never pass an unbatched two-dimensional label map.
- Prediction helpers follow the reference test order: one-hot encode the batched integer label map with the number of classes, move the class axis (currently last) to channel position 1, then scale by 1000 and cast to float. The result has shape batch, classes, spatial dimensions.
- For the optional class-dimension target variant, insert a size-1 axis after the batch axis, leaving the prediction layout unchanged.
- Tests must not use tensor methods introduced after torch 1.4, the minimum supported version.
