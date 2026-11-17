## Goals
- Add a public two-dimensional generalized Sersic surface brightness model, `GeneralSersic2D`, which extends `Sersic2D` with one extra dimensionless shape parameter `c`. Positive `c` gives "boxy" isophotes, negative `c` gives "disky" (kite-like) isophotes, and `c = 0` gives the same elliptical profile as `Sersic2D`.
- Reuse `Sersic2D`'s evaluation, parameters, and unit handling through inheritance and a generalized `Sersic2D` evaluation step. Do not build a second copy of the profile.
- Make the model available from the modeling models namespace and document it as a new feature.

## Scope
In scope:
- The new class and its public export.
- A backward-compatible generalization of `Sersic2D`'s evaluation that accepts a trailing shape argument named `c` with default 0. `Sersic2D`'s public parameter list does not change.
- Documentation: the class docstring, the See Also entry on `Sersic2D`, the 2D predefined-models page, and a changelog fragment.
- Test registrations: the generic 2D model test table, the quantity-support tests, the scipy-dependent model set, and the non-finite fitting-exception lists, plus the import lists of the two test modules that name the new class.

Out of scope:
- Changes to fitting, the model framework core, the parameter machinery, or other models.
- New range validation, public helper functions, or exception types.

## Assumptions
- Inputs follow `Sersic2D` conventions: `n > 0`, `r_eff > 0`, and `ellip` in the usual `Sersic2D` range. No extra range checks are required.
- `c` is a plain dimensionless real number.
- The reference's executable code and test values are the source of truth. Where the reference docstring formula and code differ, follow the code (see Workflows).

## Terminology
- Sersic index `n`; effective radius `r_eff`; ellipticity `ellip`, with minor-axis scale `b = (1 - ellip) * r_eff`; rotation angle `theta`; amplitude.
- Rotated coordinates `A` and `B`, and generalized radius `z`, defined in Workflows.
- Shape exponent `e = 2 + c`.
- Boxy isophote: exponent above 2 (`c > 0`), squarish. Disky (kite-like, pointed) isophote: exponent below 2 (`c < 0`). At `c = -1` the contour is a rhombus. Elliptical isophote: `c = 0`, equal to `Sersic2D`.

## Workflows
Evaluating `GeneralSersic2D` is the `Sersic2D` evaluation with `c` supplied. Pseudocode (not implementation):

    e  = 2 + c
    bn = inverse of the regularized incomplete gamma function at (2n, 0.5)
    A  = (x - x_0) * cos(theta) + (y - y_0) * sin(theta)
    B  = -(x - x_0) * sin(theta) + (y - y_0) * cos(theta)
    b  = (1 - ellip) * r_eff
    z  = ( (|A| / r_eff)^e + (|B| / b)^e ) ^ (1 / e)
    intensity = amplitude * exp( -bn * (z^(1/n) - 1) )

Requirements:
- The outer root uses the same exponent as the scaling, `1 / e`. Do not use a fixed square root, and never use `c` or `1 / c` as an exponent. At `c = 0`, `e = 2` and the result equals `Sersic2D` to floating-point rounding.
- Take absolute values of `A` and `B` before scaling by `r_eff` and `b`.
- The reference docstring writes the radius as `r^2 = |A|^(c+2) + ...`. The reference code and test values use the `1 / (2 + c)` root above. Implement the code form.
- Calling the `Sersic2D` evaluation without `c` behaves exactly as `c = 0`.

## Data model
- `GeneralSersic2D` parameters, in order: `amplitude` (default 1, "Surface brightness at r_eff"), `r_eff` (default 1, "Effective (half-light) radius"), `n` (default 4, "Sersic Index"), `x_0` (default 0, "X position of the center"), `y_0` (default 0, "Y position of the center"), `ellip` (default 0, "Ellipticity"), `theta` (default 0.0, "Rotation angle either as a float (in radians) or a |Quantity| angle"), and `c` (default 0, "Isophote shape parameter", dimensionless).
- The class body must itself declare all eight parameters with these defaults and descriptions, including the seven inherited ones. The framework builds each class's constructor signature only from that class's own declarations, so declaring only `c` would give a constructor that accepts `c` alone.
- `c` is not a parameter of `Sersic2D`, which keeps its seven parameters.

## API contracts
- `GeneralSersic2D` is a public subclass of `Sersic2D`, so an instance is also a `Sersic2D`. It is exported from the modeling models namespace.
- Construction accepts keyword arguments for all eight parameters, and also eight positional values in the order amplitude, r_eff, n, x_0, y_0, ellip, theta, c. Positional construction must bind each value to its named parameter, so `c` is the eighth positional argument.
- The `Sersic2D` evaluation takes the seven existing inputs plus a trailing argument named exactly `c` (not `shape`), default 0. It returns an intensity array with the shape of `x`, equal to `amplitude * exp(-bn * (z^(1/n) - 1))`.
- `GeneralSersic2D` does not override the evaluation, the input-units property, or the unit-to-parameter mapping. Units therefore match `Sersic2D`: `x_0`, `y_0`, and `r_eff` take the input units, `theta` is in radians, `amplitude` takes the output unit, and mismatched `x` and `y` units raise an error.
- The See Also section of `Sersic2D` names `GeneralSersic2D`.

## Module architecture
- Define the class in the functional models module, directly after `Sersic2D`.
- Add the name to the module's public export list in alphabetical order, after `Gaussian2D`. The models namespace picks it up through the existing wildcard import.
- The profile math stays in the `Sersic2D` evaluation. `GeneralSersic2D` adds the `c` declaration, the class identity, and the restated seven declarations.
- No changes to the core framework, the parameter machinery, or other modules.

## Implementation constraints
- Generalize the `Sersic2D` evaluation in place with the trailing `c` argument. Do not copy the profile body, caching, or unit hooks into the new class.
- Import the inverse incomplete gamma function from scipy lazily, inside the evaluation, so scipy stays optional. Add no module-level import.
- `Sersic2D` output for `c = 0` must be unchanged to floating-point tolerance.
- Add no validation of `c`. The reference does not handle `2 + c <= 0`, so that case is unspecified.
- Adding the model to `MODELS_WITH_CONSTRAINTS` is optional; the reference does not.

## Dependencies
- No new packages. The feature uses numpy and optional scipy, as `Sersic2D` does.

## Naming
- Class name `GeneralSersic2D`, following the `Sersic1D` and `Sersic2D` family.
- Parameter names exactly: `amplitude`, `r_eff`, `n`, `x_0`, `y_0`, `ellip`, `theta`, `c`.
- The evaluation's trailing argument is named `c`, matching the parameter.
- Test entries are keyed by the class.
- Import placement: the example-models test module and the quantity test module import model classes from explicit lists, not a wildcard. In both, add `GeneralSersic2D` immediately after `Gaussian2D`, once, with no duplicate lines. This is required because the example-models registry refers to the class by name.

## Validation
- `x` and `y` must have matching units, inherited from `Sersic2D`. No other checks are added.
- `c` is treated as a plain dimensionless number.

## Error handling
- Mismatched `x` and `y` units raise the same error type and message as `Sersic2D`. No new exception types.
- `c = 0` is valid and must not raise or produce non-finite output.

## Documentation
- The class docstring is a raw-string numpy-style docstring with Parameters, See Also (`Sersic2D`, `Gaussian2D`, `Moffat2D`), Notes (the generalized-radius formula), and References.
- The `c` description must state: negative values give disky (kite-like) isophotes, positive values give boxy isophotes, and `c = 0` gives elliptical isophotes identical to `Sersic2D`. Do not reverse these.
- Add `GeneralSersic2D` to the See Also of `Sersic2D`.
- The 2D predefined-models page gets a bullet describing `GeneralSersic2D` and its boxy or disky control, plus examples: one disky (negative `c`) and one boxy (positive `c`).
- In the predefined-models example plot, each `GeneralSersic2D` panel's title must include its own `c`, formatted as the class name, a comma, "c=" and the value with one decimal place. Use the same log normalization as `Sersic2D` and `Gaussian2D` in that example.
- Changelog: add `docs/changes/modeling/15545.feature.rst` with one or two sentences describing the model.
- Optional: a whatsnew entry in the 6.0 notes, as the reference adds.

## Performance
- No cost beyond `Sersic2D`'s current evaluation. The shared evaluation must not add per-call work.

## Maintainability
- The `Sersic2D` evaluation is the single implementation of the profile. Any later fix applies to `GeneralSersic2D` automatically. A second copy of the formula is not allowed.
- Every new or changed Python and test line must fit black's 88-column limit enforced by pre-commit. Wrap longer literals across lines.

## Reliability
- `c = 0` gives finite values equal to `Sersic2D`.
- The exponent `2 + c` is used for both scaling and the outer root. Never use `1 / c` for the root, because at `c = 0` it divides by zero.

## Usability
- The `c` sign convention is the only guide to isophote shape. The class docstring, the parameter description, and the predefined-models page must state the same convention. Users wanting disky isophotes pick negative `c`.
- Users may construct the model with keywords or with eight ordered values, as with `Sersic2D`.

## Compatibility
- `Sersic2D` parameter names, order, defaults, and outputs are unchanged. Existing `Sersic2D` construction and seven-input evaluation calls are unaffected.
- The new export is additive; no names are removed.

## Behavioral acceptance criteria
- With no arguments, `GeneralSersic2D` takes the `Sersic2D` defaults plus `c = 0`, and its values equal `Sersic2D`'s.
- For any parameters with `c = 0`, output matches `Sersic2D` to floating-point tolerance.
- Positional construction with eight values succeeds and binds the eighth value to `c`.
- `c < 0` produces pointed, kite-like (disky) contours. `c > 0` produces squarish (boxy) contours.
- Reference example: amplitude 1, r_eff 25, n 4, x_0 50, y_0 50, ellip 0.5, theta -1, c 1.0. At x values [0.0, 1, 10, 100] paired with y values [1, 100, 0.0, 10], output matches [0.01711221, 0.10471922, 0.02426327, 0.1201565] within test tolerance.
- Quantity case: amplitude 3 MJy/sr, x_0 1 arcsec, y_0 2 arcsec, r_eff 2 arcsec, n 4, c 1, ellip 0, theta 0. At (3 arcsec, 2.5 arcsec), the result is 2.9704014001846475 MJy/sr within test tolerance.
- The test modules import without error, including every module that imports the example-models test module.

## Test requirements
- Import binding comes first: the example-models test module adds `GeneralSersic2D` to its explicit import list immediately after `Gaussian2D`. Verify the name is bound before adding the registry entry, or every module importing it fails with a name error.
- Register `GeneralSersic2D` in the 2D example-model table used by the generic model tests, with the reference parameter tuple in Data model order, the reference x, y, and z values, the requires-scipy flag, and the limits. That fixture uses eight positional arguments, so positional construction must hold.
- Add a quantity-support entry with the case above and bounding box disabled. Wrap its evaluation entry across lines so no test line exceeds 88 columns.
- Add `GeneralSersic2D` to the scipy-dependent model set, and to each non-finite fitting-exception list containing `Sersic2D`: LevMar, TRF, and DogBox.
- Append `GeneralSersic2D` at the end of NON_FINITE_LM_MODELS (containing `Schechter1D`, `ExponentialCutoffPowerLaw1D`, `BrokenPowerLaw1D`), as the reference does. This list lacks `Sersic2D`, so the rule above does not cover it.
- Existing `Sersic2D` test entries remain unchanged and must pass.
