## Goals
- Add a public two-dimensional generalized Sersic surface brightness model, `GeneralSersic2D`, that extends `Sersic2D` with one extra dimensionless shape parameter `c`. Positive `c` gives "boxy" isophotes, negative `c` gives "disky" (kite-like) isophotes, and `c = 0` gives the same elliptical profile as `Sersic2D`.
- Reuse `Sersic2D`'s profile evaluation, parameters, and unit handling through inheritance and a generalized `Sersic2D` evaluation step. Do not build a second copy of the profile.
- Export the model from the modeling models namespace and document it as a new feature.

## Scope
In scope:
- The new model class and its public export.
- A backward-compatible generalization of `Sersic2D`'s evaluation that accepts a trailing shape argument named `c` with default 0. `Sersic2D`'s own public parameter list does not change.
- Documentation: the class docstring, the See Also entry on `Sersic2D`, the 2D predefined-models page, and a changelog fragment.
- Test registrations: the generic 2D model test table, the quantity-support tests, the scipy-dependent model set, and the non-finite fitting-exception lists, plus the explicit import lists that name the new class.

Out of scope:
- Changes to fitting, the model framework core, the parameter machinery, or other models.
- New range validation, public helper functions, or exception types.

## Assumptions
- Inputs follow `Sersic2D` conventions: `n > 0`, `r_eff > 0`, and `ellip` in the usual `Sersic2D` range. No extra range checks are required.
- `c` is a plain dimensionless real number.
- The reference's executable code and test values are the source of truth. Where the reference docstring formula and reference code differ, follow the code (see Workflows).

## Terminology
- Sersic index `n`; effective radius `r_eff`; ellipticity `ellip`, with minor-axis scale `b = (1 - ellip) * r_eff`; rotation angle `theta`; amplitude.
- Rotated coordinates `A` and `B`, and generalized radius `z`, defined in Workflows.
- Shape exponent `e = 2 + c`.
- Shape argument: the trailing argument of the `Sersic2D` evaluation step, named `c` to match the model parameter it receives.
- Boxy isophote: exponent above 2 (`c > 0`), squarish. Disky (kite-like, pointed) isophote: exponent below 2 (`c < 0`); at `c = -1` the contour is a rhombus. Elliptical isophote: `c = 0`, equal to `Sersic2D`.

## Workflows
Evaluating `GeneralSersic2D` is the `Sersic2D` evaluation with `c` supplied. The procedure (pseudocode, not implementation) is:

    pseudocode:
      e  = 2 + c
      bn = inverse of the regularized incomplete gamma function at (2n, 0.5)
      A  = (x - x_0) * cos(theta) + (y - y_0) * sin(theta)
      B  = -(x - x_0) * sin(theta) + (y - y_0) * cos(theta)
      b  = (1 - ellip) * r_eff
      z  = ( (|A| / r_eff)^e + (|B| / b)^e ) ^ (1 / e)
      intensity = amplitude * exp( -bn * (z^(1/n) - 1) )

Requirements:
- The outer root uses the same exponent as the scaling, `1 / e`. Do not use a fixed square root, and do not use `c` or `1 / c` as an exponent. At `c = 0`, `e = 2` and the result equals `Sersic2D` to floating-point rounding.
- Take absolute values of `A` and `B` before scaling by `r_eff` and `b`.
- The reference docstring writes the radius as `r^2 = |A|^(c+2) + ...`. The reference code and test values use the `1 / (2 + c)` root above. Implement the code form.
- Calling the `Sersic2D` evaluation without `c` behaves exactly as `c = 0`.

## Data model
- `GeneralSersic2D` parameters, in order, with defaults and descriptions:
  - `amplitude` (default 1, "Surface brightness at r_eff")
  - `r_eff` (default 1, "Effective (half-light) radius")
  - `n` (default 4, "Sersic Index")
  - `x_0` (default 0, "X position of the center")
  - `y_0` (default 0, "Y position of the center")
  - `ellip` (default 0, "Ellipticity")
  - `theta` (default 0.0, radians as a float or an angle quantity, "Rotation angle either as a float (in radians) or a |Quantity| angle")
  - `c` (default 0, "Isophote shape parameter", dimensionless)
- The class body must itself declare all eight parameters, even though the first seven are inherited from `Sersic2D`. The framework builds each class's constructor signature only from that class's own declarations, so declaring only `c` would produce a constructor accepting `c` alone.
- `c` is not a parameter of `Sersic2D`, which keeps its existing seven.

## API contracts
- `GeneralSersic2D` is a public subclass of `Sersic2D`, so an instance is also a `Sersic2D`. It is exported from the modeling models namespace.
- Construction accepts keyword arguments for all eight parameters, and also eight positional values in the order amplitude, r_eff, n, x_0, y_0, ellip, theta, c. Positional construction must bind each value to its named parameter, so `c` is the eighth positional argument.
- The `Sersic2D` evaluation step takes the seven existing inputs plus a trailing argument named exactly `c`, default 0. It returns an intensity array with the shape of `x`, equal to `amplitude * exp(-bn * (z^(1/n) - 1))`.
- `GeneralSersic2D` does not override the evaluation, the input-units property, or the unit-to-parameter mapping. Unit behavior matches `Sersic2D`: `x_0`, `y_0`, and `r_eff` take the input units, `theta` is in radians, `amplitude` takes the output unit, and mismatched `x` and `y` units raise an error.
- The See Also section of `Sersic2D` names `GeneralSersic2D`.

## Module architecture
- The class is defined in the functional models module, directly after `Sersic2D`.
- Add the name to the module's public export list in alphabetical order, after `Gaussian2D`. The models namespace picks it up through the existing wildcard import.
- The profile math stays in the `Sersic2D` evaluation. `GeneralSersic2D` adds the `c` declaration and the class identity, and restates the seven inherited declarations.
- No changes to the core framework, the parameter machinery, or other modules.

## Implementation constraints
- Generalize the `Sersic2D` evaluation in place by adding the trailing `c` argument. Do not copy the profile body, caching, or unit hooks into the new class.
- Import the inverse incomplete gamma function from scipy lazily, inside the evaluation, so scipy stays optional. Add no new module-level import.
- `Sersic2D` output for `c = 0` must be unchanged to floating-point tolerance.
- Add no validation of `c`. The reference does not handle `2 + c <= 0`, so that case is unspecified.
- Adding the model to `MODELS_WITH_CONSTRAINTS` is optional; the reference does not.

## Dependencies
- No new packages. The feature uses numpy and optional scipy, as `Sersic2D` does.

## Naming
- Class name `GeneralSersic2D`, following the `Sersic1D` and `Sersic2D` family.
- Parameter names exactly as listed under Data model.
- The evaluation's trailing argument is named `c`.
- Test entries are keyed by the class.
- The example-models test module and the quantity test module import model classes from explicit lists, not a wildcard. In both, add `GeneralSersic2D` to that list immediately after `Gaussian2D`, once only. This import is required, because the registry in the example-models module refers to the class by name.

## Validation
- `x` and `y` must have matching units, inherited from `Sersic2D`. No other checks are added.
- `c` is treated as a plain dimensionless number.

## Error handling
- Mismatched `x` and `y` units raise the same error type and message as `Sersic2D`. No new exception types.
- `c = 0` is valid input and must not raise or produce non-finite output.

## Documentation
- The class docstring is a raw-string numpy-style docstring with Parameters, See Also (`Sersic2D`, `Gaussian2D`, `Moffat2D`), Notes (the generalized-radius formula), and References.
- The `c` description must state: negative values give disky (kite-like) isophotes, positive values give boxy isophotes, and `c = 0` gives elliptical isophotes identical to `Sersic2D`. Do not reverse these.
- Add `GeneralSersic2D` to the See Also of `Sersic2D`.
- The 2D predefined-models page gets a bullet describing `GeneralSersic2D` and its boxy or disky control, and example listings with one disky example (negative `c`) and one boxy example (positive `c`).
- In the predefined-models example plot, each `GeneralSersic2D` panel title shows the class name, a comma, "c=", and its own `c` value with one decimal place. Use the same log normalization as `Sersic2D` and `Gaussian2D` in that example.
- Changelog: add `docs/changes/modeling/15545.feature.rst` with one or two sentences describing the model.
- Optional: a whatsnew entry in the 6.0 notes, as the reference adds.

## Performance
- No cost beyond `Sersic2D`'s current evaluation. The shared evaluation must not add per-call work.

## Maintainability
- The `Sersic2D` evaluation is the single implementation of the profile. `GeneralSersic2D` inherits it, so later fixes apply to both. No second copy of the formula.
- Every new or changed line of Python and test code must fit the repository's black line length of 88 columns. Wrap longer literals across several lines.

## Reliability
- `c = 0` gives finite values equal to `Sersic2D`.
- The exponent `2 + c` is used for both scaling and the outer root. The outer root must never be `1 / c`, which divides by zero at `c = 0`.

## Usability
- The `c` sign convention is the only guide a user has to isophote shape. The class docstring, the parameter description, and the predefined-models page must all state the same convention. Disky isophotes require negative `c`.
- A user can construct the model with keywords or with the eight values in order, as with `Sersic2D`.

## Compatibility
- `Sersic2D` parameter names, order, defaults, and outputs are unchanged. Existing `Sersic2D` construction and seven-input evaluation calls are unaffected.
- The new export is additive. No names are removed.

## Behavioral acceptance criteria
- With no arguments, `GeneralSersic2D` takes the `Sersic2D` defaults plus `c = 0`, and its values equal `Sersic2D` at the same parameters.
- For any parameters with `c = 0`, output matches `Sersic2D` to floating-point tolerance.
- Positional construction with eight values succeeds and binds the eighth value to `c`.
- `c < 0` produces pointed, kite-like (disky) contours. `c > 0` produces squarish (boxy) contours.
- Reference example: amplitude 1, r_eff 25, n 4, x_0 50, y_0 50, ellip 0.5, theta -1, c 1.0. At x values [0.0, 1, 10, 100] paired with y values [1, 100, 0.0, 10], output matches [0.01711221, 0.10471922, 0.02426327, 0.1201565] within test tolerance.
- Quantity case: amplitude 3 MJy/sr, x_0 1 arcsec, y_0 2 arcsec, r_eff 2 arcsec, n 4, c 1, ellip 0, theta 0. At (3 arcsec, 2.5 arcsec), the result is 2.9704014001846475 MJy/sr within test tolerance.
- The example-models test module and each module that imports it load without error.

## Test requirements
- Import binding comes first: the example-models test module must bind `GeneralSersic2D` through its explicit import list, immediately after `Gaussian2D`. Otherwise the registry entry raises a name error that breaks every module importing it. Verify the binding before adding the registry entry.
- Register `GeneralSersic2D` in the 2D example-model table used by the generic model tests, using the reference parameter tuple in Data model order, the reference x, y, and z values, the requires-scipy flag, and the limits. That fixture passes the eight values positionally, so positional construction must hold.
- Add a quantity-support entry with the case above and bounding box disabled. Wrap its evaluation entry across several lines so no line exceeds 88 columns.
- Add `GeneralSersic2D` to the scipy-dependent model set, and to each non-finite fitting-exception list that contains `Sersic2D`: the LevMar, TRF, and DogBox lists.
- Add `GeneralSersic2D` to the end of the LMLSQFitter list `NON_FINITE_LM_MODELS`, as the reference does. That list does not contain `Sersic2D`, so this must be added explicitly.
- Existing `Sersic2D` test entries remain unchanged and must pass.
