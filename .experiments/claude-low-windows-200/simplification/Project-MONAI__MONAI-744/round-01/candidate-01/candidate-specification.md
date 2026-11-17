# Generalized Wasserstein Dice Loss

## Goals
- Add GeneralizedWassersteinDiceLoss to MONAI's losses package. It computes a Dice-type overlap score in which each voxel's true-positive contribution is discounted by a Wasserstein distance between the predicted class distribution and the ground-truth label, using a class-distance matrix. Per-class weights follow the generalized Dice weighting (inverse volume).
- Usage matches existing segmentation losses: raw logits in, integer class-index label maps as targets, a scalar loss out.
- Export the class from the losses package and define a lowercase alias in the dice module.

## Scope
In scope:
- One new class in the dice module, placed after the existing generalized Dice class.
- Two new imports in the dice module (numpy and the torch functional module).
- The package export in the losses package initializer, and the lowercase module-level alias.
- One new unit test module.

Out of scope:
- Any change to existing loss classes, the LossReduction enum, or shared utilities.
- Weight-type, masking, sigmoid, softmax, or one-hot option flags on the new class.
- Edits to docs/source pages. In-code docstrings are in scope (see Documentation).
- New third-party packages.

## Assumptions
- Input is a floating-point logits tensor of shape batch, classes, then zero or more spatial dimensions. The number of spatial dimensions is unrestricted.
- Input and target both carry a leading batch axis, and the batch sizes match. Unbatched label maps are outside the contract. The reference reads the target's first axis as the batch axis, so an unbatched two-dimensional label map is misread as a batch of its rows. Do not accept, reshape, or work around unbatched targets.
- Target is an integer tensor of class indices, shape batch, spatial dimensions, or batch, 1, spatial dimensions. Both forms are accepted.
- The distance matrix is square, C by C, where C is the number of input channels. Entries are nonnegative. It is a 2D torch tensor or 2D numpy array.
- Label values lie in 0 to C minus 1. The reference does not check this.

## Terminology
- Logits: raw network outputs. Softmax over the class dimension gives probabilities.
- Distance matrix m: the C by C class-distance matrix after optional max normalization.
- Wasserstein distance map W_s(v): for sample s and voxel v with ground-truth label y_s(v), W_s(v) equals the sum over classes k of m[y_s(v), k] times p_k,s(v), where p_k,s(v) is the softmax probability of class k at that voxel. W is computed for every sample.
- Volume V(b, c): the number of voxels in sample b whose label is c.
- Class weight alpha(b, c): 1 divided by (V(b, c) + 1). A class absent from a sample has weight 1.
- Generalized true positives TP_b: for each sample b, the sum over every sample index s in the batch and every voxel v of alpha(b, y_b(v)) times (1 minus W_s(v)). The weight uses sample b's own labels and volumes; the distance term comes from every sample s. This cross-sample coupling is the reference behavior and is intentional for parity. Do not replace it with a sum over each sample's own distance map. For a batch of one, s ranges over sample b only.
- Denominator D_b: the same sum with (2 minus W_s(v)) in place of (1 minus W_s(v)), with the same cross-sample coupling.

## Workflows
Construction:
1. Convert the reduction setting through the shared LossReduction conversion and pass it to the parent initializer. Invalid reduction values fail here, before the matrix check.
2. Check that the distance matrix is square; otherwise raise an error (see Error handling).
3. If the matrix is numpy, convert it to a torch tensor.
4. If the maximum entry is not exactly 1, divide the whole matrix by its maximum. Otherwise leave it unchanged.
5. Store the normalized matrix as m and the matrix size as num_classes.

Forward (input, target, smooth default 1e-5):
1. Flatten input to batch by classes by N, where N is the product of the spatial sizes. Flatten target to batch by N, accepting both target shapes. Key on the first axis as the batch axis.
2. Apply softmax over the class dimension. The input is always treated as logits; no flag changes this.
3. Compute the Wasserstein distance map W for every sample and voxel using m, moved to the probabilities' device at call time. Result: batch by N.
4. Compute alpha per sample and class from label counts. Empty classes get weight 1, not a sentinel.
5. Compute TP_b and D_b for every sample b using the cross-sample rule. For each b, pair its per-voxel alpha map (from its own labels) with the distance maps of all samples s, form the products with (1 minus W) for TP or (2 minus W) for D over the (b, s, voxel) combinations, and sum over s and voxel. Output is one value per sample. Do not compute TP or D from each sample's own distance map alone.
6. For each sample, score = (2 times TP_b plus smooth) divided by (D_b plus smooth); per-sample loss = 1 minus score.
7. Return the mean of per-sample losses as a scalar tensor. Reduction is stored but not applied in forward.

The four helper methods in API contracts carry out steps 3 to 5, and forward calls them.

## Data model
- Stored state: the normalized matrix m (C by C, same tensor type as after numpy conversion), num_classes, and the reduction string.
- Input: float logits, shape batch, classes, spatial dimensions.
- Target: integer class-index labels, shape batch, spatial dimensions, or batch, 1, spatial dimensions. One-hot targets are not part of the contract.
- Output: one scalar tensor.

## API contracts
- Class GeneralizedWassersteinDiceLoss inherits from the same torch loss base class as the sibling loss classes.
- Constructor takes exactly two parameters, in this order:
  - dist_matrix, first, required, no default. Accepts a 2D torch tensor or 2D numpy array.
  - reduction, second, default MEAN. Accepts a LossReduction member or its string value. It is passed to the parent and stored, but does not change forward's return value, which is always the batch mean.
- No other constructor parameters. Weight-type, include-background, to-one-hot, sigmoid, and softmax flags are not part of this class. Changing the position of reduction breaks callers.
- forward takes input, target, and smooth (default 1e-5). smooth belongs to forward, as in the sibling Generalized Dice loss. forward returns a scalar tensor.
- Public helper methods:
  - wasserstein_distance_map: takes flattened probabilities (batch by classes by N) and flattened target (batch by N); returns per-voxel distances for every sample (batch by N).
  - compute_weights_generalized_true_positives: takes flattened target; returns alpha weights (batch by classes).
  - compute_generalized_true_positive: takes alpha, flattened target, and the full batch distance map (batch by N); returns one TP per sample (shape batch), using the cross-sample rule.
  - compute_denominator: takes alpha, flattened target, and the full batch distance map; returns one D per sample (shape batch), using the cross-sample rule.
- Instance attributes: m and num_classes.
- Module-level name generalized_wasserstein_dice refers to the class. It is defined in the dice module only, not added to losses package exports.

## Module architecture
- Location: the dice module, after the generalized Dice class and before the module-level alias block.
- Self-contained: does not call other loss classes or add module-level helper functions.
- Reuse the shared LossReduction enum from monai utilities.
- Package wiring: the losses package initializer imports the new class from the dice module next to existing dice exports, and exports GeneralizedWassersteinDiceLoss. Existing exported names are unchanged.

## Implementation constraints
- Use vectorized tensor operations over batch and voxels. No Python loops over voxels or samples.
- Label indices are used only as gather or indexing keys and must be integer typed.
- Compute alpha from counts only, with no sentinel or large constant weights.
- No shape, dtype, or label-range validation inside forward. Targets, batch-1-spatial targets, and logits reach the computation unchanged.
- No sigmoid, one-hot conversion, or weight-type options. No reduction inside forward; do not reproduce sibling reduction branches.
- TP and D must couple samples as described in Terminology. A per-sample-only computation is not acceptable, even though it is the more common form of the formula.
- Use gather-style indexing for the distance lookup (each voxel's row of m chosen by its label) and for alpha lookup in TP and D.
- Moving m to the probability device on each call must leave the stored matrix unchanged.

## Dependencies
- Newly imports numpy and the torch functional module, both existing MONAI dependencies. No new package.
- Use torch's functional one-hot for label counting.
- Use the existing LossReduction enum from monai utilities.

## Naming
- Class: GeneralizedWassersteinDiceLoss, matching sibling classes.
- Alias: generalized_wasserstein_dice, matching the generalized_dice alias pattern.
- Methods: the snake_case names in API contracts.
- Attributes: m and num_classes.
- Parameters: dist_matrix, reduction, smooth, input, target, and the reference's helper parameter names (alpha, flat_target, flat_proba, wasserstein_distance_map).

## Validation
- Constructor checks only that the matrix is square.
- Reduction is validated only through the shared LossReduction conversion.
- forward performs no dtype, device, shape, or label validation; invalid inputs fail in tensor operations.

## Error handling
- Non-square matrix: ValueError with message "Dist Matrix is invalid."
- Invalid reduction: the ValueError from the LossReduction conversion.
- Tensor-operation errors inside forward propagate unchanged. Do not wrap or pre-check them.

## Documentation
- Class docstring: state the purpose and cite Fidon et al., Generalised Wasserstein Dice Score, MICCAI BrainLes 2017, and Sudre et al., Generalised Dice overlap, MICCAI DLMIA 2017. Note that weighting follows the generalized Dice loss.
- Each helper has a short docstring with an Args section in sibling style.
- compute_generalized_true_positive and compute_denominator docstrings state that the sum runs over every sample's distance map in the batch, so each value depends on the whole batch.
- Constructor docstring documents dist_matrix (square, tensor or numpy), names reduction as the reduction mode, lists the ValueError under Raises, does not list "none" or "sum" as output modes, and states the returned loss is the batch mean regardless of reduction.
- Keep added lines within 120 columns.
- Do not edit docs/source/losses.rst. Existing autodoc entries, including generalized_dice and its members option, stay as they are.

## Performance
- Cost is batch times batch times voxels for the cross-sample TP and D terms, plus batch times classes times voxels for other steps.
- Distance lookup and alpha lookup use gather-style indexing; no per-voxel loops.

## Reliability
- smooth is added to numerator and denominator to avoid division by zero.
- Softmax keeps probabilities in [0, 1] for any logits. A batch where every sample is confidently correct gives a loss near 0; confidently wrong gives near 1.

## Maintainability
- Keep the four helper methods as separate steps so each can be checked alone.
- Keep docstrings describing each stage's formula, including the batch-wide sum for TP and D.

## Compatibility
- Additive change. No existing class signature, export, or alias changes.
- Constructor positional order (dist_matrix, then reduction) is a public contract.

## Operations
- No runtime configuration or environment variables.
- Output is on the same device as the input logits.

## Behavioral acceptance criteria
- Binary 2D case: batch of one; 4 by 4 target with inner 2 by 2 block labeled 1 and the rest 0, shape batch 1, 4, 4. Distance matrix 2 by 2, zero on diagonal, 1 off it. Logits equal 1000 times the one-hot of the target with class axis moved to channel position 1 (logit shape batch 1, classes 2, 4, 4). Loss is 0 to 3 decimal places. The same target with an added size-1 channel dimension (shape batch 1, 1, 4, 4) gives the same result. Logits equal to 1000 times the one-hot of the flipped target give 1 to 3 decimal places.
- Empty class case: 4 by 4 all-zero target, two classes, batch axis of size 1. Logits as above give 0 to 3 decimal places; flipped logits give 1 to 3 decimal places.
- Batch-coupling case (batch of two): same 2 by 2 matrix. Sample 0 is an all-zero 2 by 2 target; sample 1 is an all-one 2 by 2 target. Logits for sample 0 are 1000 times the one-hot of class 0 at every voxel (correct). Logits for sample 1 are also 1000 times the one-hot of class 0 at every voxel (wrong). Expected loss approximately 0.333 to 3 decimal places. Each sample's TP is 0.8 and D is 2.4 under the cross-sample rule. A per-sample-only computation gives 0.5 and fails this criterion.
- A numpy distance matrix and an equivalent tensor give the same loss.
- A matrix with maximum 2 (zero diagonal, 2 off it) gives the same loss as its max-normalized form.
- Non-square matrix raises ValueError at construction.
- Returned value is scalar; changing reduction (mean, sum, none) does not change it.
- Constructor docstring meets the Documentation rules.
- Module-level alias is the same object as the class.

## Test requirements
- Add tests/test_generalized_wasserstein_dice_loss.py following sibling test conventions: 2020 MONAI Consortium license header, unittest, a test class, and a main guard.
- Two tests: binary 2D case and empty class case, with the scenarios and 3-decimal tolerance above.
- Targets are integer label maps with a leading batch axis (size 1) before any one-hot step. Never pass an unbatched 2D label map to the loss or a test helper.
- Prediction helpers: take the batched integer label map, one-hot encode with the number of classes, move the one-hot class axis (currently last) to channel position 1, then scale by 1000 and cast to float. Result shape batch, classes, spatial dimensions; channel count must equal the number of classes (2). Verify by reading the helper and its calls.
- Optional class-dimension target variant: insert a size-1 axis after the batch axis. Do not change the prediction layout.
- Tests must not use tensor methods newer than torch 1.4, the declared minimum.
- Tests are in the patch but not required to run in the harness.
