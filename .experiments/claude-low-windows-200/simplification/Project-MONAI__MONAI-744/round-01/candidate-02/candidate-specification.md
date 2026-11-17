# Generalized Wasserstein Dice Loss

## Goals
- Add GeneralizedWassersteinDiceLoss to MONAI's losses package. It computes a Dice-type overlap score in which each voxel's true-positive contribution is discounted by a Wasserstein distance between the predicted class distribution and the ground-truth label, using a class-distance matrix. Class weights follow the generalized Dice weighting (inverse volume).
- Usage matches existing segmentation losses: raw logits in, integer class-index label maps as targets, a scalar loss out.
- Export the class from the losses package and define a lowercase alias in the dice module.

## Scope
In scope:
- One new class in the dice module, placed after the generalized Dice class.
- Two new imports in the dice module (numpy and the torch functional module).
- The package export in the losses package initializer.
- The lowercase module-level alias.
- One new unit test module.

Out of scope:
- Any change to existing loss classes, the LossReduction enum, or shared utilities.
- Weight-type, masking, sigmoid, softmax, or one-hot option flags on the new class.
- Edits to docs/source. In-code docstrings are in scope (see Documentation).
- New third-party packages.

## Assumptions
- Input is a floating-point logits tensor with shape batch, classes, then zero or more spatial dimensions.
- Input and target both carry a leading batch axis, and the batch sizes match. Unbatched label maps are outside the contract. Do not accept, reshape, or work around them.
- Target is an integer tensor of class indices with shape batch, spatial dimensions, or batch, 1, spatial dimensions. Both forms are accepted.
- The distance matrix is square, size C by C, where C is the number of input channels. Entries are nonnegative. It is a 2D torch tensor or a 2D numpy array.
- Label values lie in 0 to C minus 1. The reference does not check this.

## Terminology
- Logits: raw network outputs. Softmax over the class dimension gives probabilities p_k(v).
- Distance matrix M: the C by C class-distance matrix, after optional max normalization.
- Wasserstein distance map W_s(v): for sample s and voxel v with ground-truth label y_s(v), the sum over classes k of M[y_s(v), k] times p_k,s(v). W is computed for every sample.
- Volume V(b, c): the number of voxels in sample b whose label is c.
- Class weight alpha(b, c): 1 divided by (V(b, c) + 1). A class absent from a sample has weight 1.
- Generalized true positives TP_b: the sum over every sample index s in the batch and every voxel v of alpha(b, y_b(v)) times (1 minus W_s(v)). The weight uses sample b's labels and volumes; the distance term comes from every sample s. This cross-sample coupling is the reference behavior and is intentional. A sum over each sample's own distance map is not acceptable. For a batch of one, s ranges over sample b only.
- Denominator D_b: the same sum with (2 minus W_s(v)) in place of (1 minus W_s(v)), with the same cross-sample coupling.

## Workflows
Construction:
1. Pass the reduction setting to the parent loss initializer through the shared LossReduction conversion, so the stored value is the enum's string value. Invalid reduction values fail here, before the matrix check.
2. Check that the matrix is square (see Error handling).
3. If the matrix is numpy, convert it to a torch tensor.
4. If the maximum entry is not exactly 1, divide the whole matrix by that maximum. Otherwise leave it unchanged.
5. Store the normalized matrix as m and the matrix size as num_classes.

Forward (arguments: input, target, smooth with default 1e-5):
1. Flatten input to batch by classes by N, where N is the product of the spatial sizes. Flatten target to batch by N, accepting both target shapes.
2. Apply softmax over the class dimension. The input is always treated as logits.
3. Compute W for every sample and voxel using m, moved to the probabilities' device at call time. The result has shape batch by N.
4. Compute alpha from label counts per sample and class. Empty classes get weight 1, not a sentinel.
5. Compute TP_b and D_b for every sample b using the cross-sample rule. For each sample b, pair its weight map (alpha of its own labels) with the distance maps of all samples s, form the product with (1 minus W) for TP or (2 minus W) for D over the (b, s, voxel) combinations, and sum over s and voxel. The result has one value per sample.
6. For each sample, compute the score (2 times TP_b plus smooth) divided by (D_b plus smooth). The per-sample loss is 1 minus that score.
7. Return the mean of the per-sample losses as a scalar tensor. Reduction is stored but not applied in forward.

## Data model
- Stored state: the normalized matrix m (C by C, torch tensor), num_classes, and the reduction string.
- Input: float logits, shape batch, classes, spatial dimensions.
- Target: integer class-index labels, shape batch, spatial dimensions, or batch, 1, spatial dimensions. One-hot targets are not supported.
- Output: one scalar tensor.

## API contracts
- The class is named GeneralizedWassersteinDiceLoss and inherits from the same torch loss base class as the sibling loss classes.
- Constructor parameters, in this order (position matters for callers):
  - dist_matrix: required, no default. A 2D torch tensor or 2D numpy array.
  - reduction: default MEAN. Accepts a LossReduction member or its string value. It is passed to the parent and stored, but forward always returns the batch mean.
- No other constructor parameters. Weight-type, include-background, one-hot, sigmoid, and softmax flags are not part of this class.
- forward(input, target, smooth=1e-5) returns a scalar tensor. smooth belongs to forward, as in the sibling Generalized Dice loss.
- Public helper methods:
  - wasserstein_distance_map: takes flattened probabilities (batch by classes by N) and flattened target (batch by N); returns per-voxel distances (batch by N).
  - compute_weights_generalized_true_positives: takes flattened target; returns alpha weights (batch by classes).
  - compute_generalized_true_positive: takes alpha, flattened target, and the full batch distance map (batch by N); returns one TP per sample (shape batch), using the cross-sample rule.
  - compute_denominator: takes the same arguments; returns one D per sample (shape batch), using the cross-sample rule.
- Instance attributes: m and num_classes.
- The module-level name generalized_wasserstein_dice refers to the class. It is defined in the dice module only, not added to the losses package exports.
- The losses package exports GeneralizedWassersteinDiceLoss.

## Module architecture
- Location: the dice module, after the generalized Dice class and before the alias block.
- Self-contained: no calls to other loss classes and no module-level helper functions.
- Use the shared LossReduction enum from monai utilities for reduction.
- The losses package initializer imports the new class from the dice module next to the existing dice exports. Existing exported names are unchanged.

## Implementation constraints
- Use vectorized tensor operations over batch and voxels. No Python loops over voxels or samples.
- Use class labels only as gather or indexing keys; they must be integer typed.
- Use torch's functional one-hot for label counting.
- Do not add shape, dtype, device, or label-range validation inside forward. Invalid inputs fail in the tensor operations, and their errors propagate unchanged.
- Do not add sigmoid, one-hot conversion, or weight-type options.
- Do not apply reduction inside forward, and do not reproduce the sibling classes' reduction branches.
- Keep the stored matrix unchanged; move a copy to the probability device on each forward call.

## Dependencies
- The dice module newly imports numpy and the torch functional module. Both are existing MONAI dependencies.
- Use the existing LossReduction enum from monai utilities.

## Naming
- Class: GeneralizedWassersteinDiceLoss. Alias: generalized_wasserstein_dice, matching the generalized_dice alias pattern.
- Methods: the snake_case names in API contracts.
- Attributes: m and num_classes.
- Parameters: dist_matrix, reduction, smooth, input, target, and the helper parameter names used in the reference (alpha, flat_target, flat_proba, wasserstein_distance_map).

## Validation
- The constructor checks only that the matrix is square.
- Reduction is validated only through the shared LossReduction conversion.

## Error handling
- A non-square distance matrix raises ValueError with the message "Dist Matrix is invalid."
- An invalid reduction raises the ValueError from the LossReduction conversion.

## Documentation
- The class docstring states the purpose, cites Fidon et al., Generalised Wasserstein Dice Score, MICCAI BrainLes 2017, and Sudre et al., Generalised Dice overlap, MICCAI DLMIA 2017, and notes the weighting follows the generalized Dice loss.
- Each helper has a short docstring with an Args section in the sibling style.
- The docstrings of compute_generalized_true_positive and compute_denominator state that the sum runs over every sample's distance map in the batch.
- The constructor docstring documents the distance matrix (square, tensor or numpy), names reduction as the reduction mode, and lists the ValueError under Raises. It must not list "none" or "sum" as output modes. It must state that the returned loss is the batch mean regardless of reduction.
- Keep every added line within 120 columns.
- Do not edit docs/source/losses.rst. Existing autodoc entries, including generalized_dice and its members option, stay as they are.

## Performance
- Cost is proportional to batch times batch times voxels for the TP and D terms, plus batch times classes times voxels for other steps.
- Use gather-style indexing: the distance helper picks each voxel's matrix row by its label; the TP and D helpers pick each voxel's alpha by its label.

## Reliability
- smooth is added to numerator and denominator to avoid division by zero.
- Softmax keeps probabilities in [0, 1]. A batch where every sample is confidently correct gives a loss near 0; one where every sample is confidently wrong gives a loss near 1.

## Maintainability
- Keep the four helpers as separate stages, each with a docstring stating its formula, including the batch-wide sum for TP and D.

## Compatibility
- The change is additive. No existing signature, export, or alias changes.

## Operations
- No runtime configuration or environment variables.
- Output is on the same device as the input logits.

## Behavioral acceptance criteria
- Binary 2D case: batch of one, a 4 by 4 target whose inner 2 by 2 block is label 1 and rest is label 0 (shape batch 1, 4, 4). Distance matrix is 2 by 2, zero on the diagonal and 1 off it. Logits are 1000 times the one-hot of the target with the class axis at channel position 1 (shape batch 1, classes 2, 4, 4). Loss is 0 to 3 decimal places. The same target with an added size-1 channel dimension (shape batch 1, 1, 4, 4) gives the same result. Logits from the one-hot of the flipped target give 1 to 3 decimal places.
- Empty class case: a 4 by 4 all-zero target with batch axis 1 and two classes. Logits from the one-hot of the target give 0 to 3 decimal places. Flipped logits give 1 to 3 decimal places.
- Batch-coupling case (batch of two): with the same 2 by 2 matrix, sample 0 is an all-zero 2 by 2 target with logits 1000 times the one-hot of class 0 (correct). Sample 1 is an all-one 2 by 2 target with logits 1000 times the one-hot of class 0 (wrong). Expected loss is 0.333 to 3 decimal places, with TP 0.8 and D 2.4 per sample under the cross-sample rule. A per-sample-only computation gives 0.5 and fails this criterion.
- A numpy matrix and an equivalent tensor give the same loss.
- A matrix whose maximum is 2 (zero diagonal, 2 off it) gives the same loss as its max-normalized form.
- A non-square matrix raises ValueError at construction.
- The returned value is a scalar, and changing reduction (mean, sum, or none) does not change it.
- The constructor docstring lists no none or sum outputs and states the batch mean.
- The alias generalized_wasserstein_dice is the same object as the class.

## Test requirements
- Add tests/test_generalized_wasserstein_dice_loss.py following the sibling test convention: 2020 MONAI Consortium license header, unittest, a test class, and a main guard.
- Two tests: the binary 2D case and the empty class case, with the scenarios and 3-decimal tolerance above.
- Targets are integer label maps with a leading batch axis (size 1) before any one-hot step. Never pass an unbatched 2D label map to the loss or to a helper.
- Helpers that build class-first predictions take the batched label map, one-hot encode it with the class count, move the one-hot class axis (last) to channel position 1, then scale by 1000 and cast to float. The channel count must equal the class count (2). Verify by reading the helper and its calls.
- For the class-dimension target variant, insert a size-1 axis after the batch axis. Do not change the prediction layout.
- Use no tensor methods introduced after torch 1.4.
- Tests are part of the patch; the harness need not run them.
