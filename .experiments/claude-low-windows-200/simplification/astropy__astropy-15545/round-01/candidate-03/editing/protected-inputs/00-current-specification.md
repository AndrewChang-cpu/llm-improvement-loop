## Goals
- Add a public two-dimensional generalized Sersic surface brightness model, `GeneralSersic2D`, that extends the existing `Sersic2D` with one extra dimensionless shape parameter `c`. Positive `c` gives "boxy" isophotes, negative `c` gives "disky" (kite-like) isophotes, and `c = 0` gives the same elliptical profile as `Sersic2D`.
- Reuse `Sersic2D`'s profile evaluation, parameters, and unit handling through inheritance and a generalized `Sersic2D` evaluation step. Do not build a second, parallel copy of the profile.
- Make the model available from the modeling models namespace and document it as a new feature.

## Scope
In scope:
- The new model class and its public export.
- A backward-compatible generalization of `Sersic2D`'s evaluation so it accepts a trailing shape argument named `c` with default 0. `Sersic2D`'s own public parameter list does not change.
- Documentation: the class docstring, the See Also entry on `Sersic2D`, the 2D predefined-models page, and a changelog fragment.
- Test registrations: the generic 2D model test table, the quantity-support tests, the scipy-dependent model set, and the non-finite fitting-exception lists. The import lists of the two test modules that name the new class are also in scope.

Out of scope:
- Changes to fitting, the model framework core, the parameter machinery, or other models.
- New range validation, new public helper functions, or new exception types.

## Assumptions
- Inputs follow `Sersic2D` conventions: `n > 0`, `r_eff > 0`, and `ellip` in the usual range for `Sersic2D`. No extra range checks are required.
- `c` is a dimensionless real number. Plain numbers are passed for it.
- The reference's executable code and its test values are the source of truth for numbers. Where the reference docstring formula and the reference code differ, follow the code (see Workflows).

## Terminology
- Sersic index `n`; effective radius `r_eff`; ellipticity `ellip`, with minor-axis scale `b = (1 - ellip) * r_eff`; rotation angle `theta`; amplitude.
- Rotated coordinates `A` and `B`, defined in Workflows.
- Generalized radius `z`.
- Shape exponent `e = 2 + c`.
- Shape argument: the trailing argument of the `Sersic2D` evaluation step. It is named `c`, the same name as the model parameter it receives.
- Boxy isophote: a contour with exponent above 2 (`c > 0`). It is squarish.
- Disky (kite-like, pointed) isophote: a contour with exponent below 2 (`c < 0`). At `c = -1` the contour is a rhombus.
- Elliptical isophote: the case `c = 0`, which equals `Sersic2D`.

## Workflows
Evaluating `GeneralSersic2D` is the `Sersic2D` evaluation with `c` supplied. The procedure is (pseudocode, not implementation):

    pseudocode:
      e  = 2 + c
      bn = inverse of the regularized incomplete gamma function at (2n, 0.5)
      A  = (x - x_0) * cos(theta) + (y - y_0) * sin(theta)
      B  = -(x - x_0) * sin(theta) + (y - y_0) * cos(theta)
      b  = (1 - ellip) * r_eff
      z  = ( (|A| / r_eff)^e + (|B| / b)^e ) ^ (1 / e)
      intensity = amplitude * exp( -bn * (z^(1/n) - 1) )

Requirements for this procedure:
- The outer root uses the same exponent as the scaling, namely `1 / e`. Do not use a fixed square root. Do not use `c` or `1 / c` as an exponent. At `c = 0`, `e = 2` and the result equals `Sersic2D` to floating-point rounding.
- Take the absolute values of `A` and `B` before scaling by `r_eff` and `b`.
- The reference docstring writes the generalized radius as `r^2 = |A|^(c+2) + ...`. The reference code and its test values use the `1 / (2 + c)` root above. Implement the code form.
- Calling the `Sersic2D` evaluation without `c` behaves exactly as `c = 0`.

## Data model
- `GeneralSersic2D` parameters, in order: `amplitude` (default 1, "Surface brightness at r_eff"), `r_eff` (default 1, "Effective (half-light) radius"), `n` (default 4, "Sersic Index"), `x_0` (default 0, "X position of the center"), `y_0` (default 0, "Y position of the center"), `ellip` (default 0, "Ellipticity"), `theta` (default 0.0, radians as a float or an angle quantity, "Rotation angle either as a float (in radians) or a |Quantity| angle"), and `c` (default 0, "Isophote shape parameter", dimensionless).
- The class body of `GeneralSersic2D` must itself declare all eight parameters, in the order above, each with its stated default and description. The first seven are restated in the class body even though `Sersic2D` already declares them. Inheriting the seven `Sersic2D` declarations and declaring only `c` is not acceptable: the framework builds each class's constructor signature only from that class's own parameter declarations, so a subclass that declares only `c` gets a constructor that accepts `c` alone.
- `c` is not a parameter of `Sersic2D`. `Sersic2D` keeps only its existing seven parameters.

## API contracts
- `GeneralSersic2D` is a public subclass of `Sersic2D`, so an instance is also an instance of `Sersic2D`. It is exported from the modeling models namespace.
- Construction: the constructor accepts keyword arguments for all eight parameters and also accepts eight positional values in the order amplitude, r_eff, n, x_0, y_0, ellip, theta, c. Positional construction with eight values must succeed without error and bind each value to its named parameter, so `c` is the eighth positional argument. This matches `Sersic2D`'s positional behavior, extended by one.
- The `Sersic2D` evaluation step takes the seven existing inputs plus a trailing argument named `c` with default 0. The argument is named exactly `c`, not `shape` or any other name, so it matches the model parameter name. It returns an intensity array with the shape of `x`, equal to `amplitude * exp(-bn * (z^(1/n) - 1))`.
- `GeneralSersic2D` does not override the evaluation, the input-units property, or the unit-to-parameter mapping. It inherits them, so unit behavior matches `Sersic2D`: `x_0`, `y_0`, and `r_eff` take the input units, `theta` is in radians, `amplitude` takes the output unit, and mismatched `x` and `y` units raise an error.
- The `See Also` section of `Sersic2D` names `GeneralSersic2D`.

## Module architecture
- Location: the class is defined in the functional models module, directly after `Sersic2D`.
- Export: add the name to the module's public export list in alphabetical order, after `Gaussian2D`. The models namespace picks it up through the existing wildcard import.
- Responsibilities: the profile math stays in the `Sersic2D` evaluation. `GeneralSersic2D` adds the `c` parameter declaration and the class identity; it restates the seven inherited parameter declarations as described under Data model.
- No changes to the core model framework, the parameter machinery, or other modules.

## Implementation constraints
- Generalize the `Sersic2D` evaluation in place by adding the trailing shape argument named `c` with default 0. Do not copy the profile body, the caching, or the unit hooks into the new class.
- Import the inverse incomplete gamma function from scipy lazily, inside the evaluation, so scipy stays optional. Add no new module-level import.
- `Sersic2D` output for `c = 0` must be unchanged to floating-point tolerance.
- Add no validation of `c`. The reference does not handle `2 + c <= 0`, so that case is not specified.
- Adding the model to the constraints list (`MODELS_WITH_CONSTRAINTS` in the models package) is optional. The reference does not add it.

## Dependencies
- No new packages or required dependencies. The feature uses numpy and optional scipy, the same as `Sersic2D`.

## Naming
- Class name `GeneralSersic2D`, following the `Sersic1D` and `Sersic2D` family.
- Parameter names exactly: `amplitude`, `r_eff`, `n`, `x_0`, `y_0`, `ellip`, `theta`, `c`.
- The evaluation's trailing argument is named `c`, matching the parameter.
- Test entries are keyed by the class.
- Import placement: the example-models test module and the quantity test module each import their model classes from an explicit list, not a wildcard. In both modules, `GeneralSersic2D` must be added to that explicit list immediately after `Gaussian2D`, keeping the list alphabetical. Import the name exactly once in each module; no duplicate import lines. This import is required, not optional, because the test registry in the example-models module refers to the class by name (see Test requirements).

## Validation
- `x` and `y` must have matching units. This check is inherited from `Sersic2D`. No other checks are added.
- `c` is treated as a plain dimensionless number.

## Error handling
- Mismatched `x` and `y` units raise the same error type and message as `Sersic2D`. Add no new exception types.
- `c = 0` is valid input and must not raise or produce non-finite output.

## Documentation
- The class docstring is a raw-string numpy-style docstring with Parameters, See Also (`Sersic2D`, `Gaussian2D`, `Moffat2D`), Notes (the generalized-radius formula), and References.
- The `c` description must state: negative values give disky (kite-like) isophotes, positive values give boxy isophotes, and `c = 0` gives elliptical isophotes identical to `Sersic2D`. Do not reverse these.
- Add `GeneralSersic2D` to the See Also of `Sersic2D`.
- The 2D predefined-models page gets a bullet describing `GeneralSersic2D` and its boxy or disky control. Add it to the example listing with one disky example (negative `c`) and one boxy example (positive `c`).
- In the predefined-models example plot, each `GeneralSersic2D` panel must have a title that includes its own `c` value, formatted as the class name, a comma, "c=" and the value with one decimal place. Without this the two panels cannot be told apart. Give `GeneralSersic2D` the same log normalization used for `Sersic2D` and `Gaussian2D` in that example.
- Changelog: add a fragment named by the pull request number, `docs/changes/modeling/15545.feature.rst`, with one or two sentences describing the new model.
- Optional: a whatsnew entry in the 6.0 notes, as the reference adds.

## Performance
- No requirement beyond `Sersic2D`'s current evaluation cost. The shared evaluation must not add per-call work that `Sersic2D` does not already do.

## Maintainability
- The `Sersic2D` evaluation is the single implementation of the profile. `GeneralSersic2D` inherits it, so any later fix to `Sersic2D` also applies to `GeneralSersic2D`. A second copy of the formula is not allowed.
- Every new or changed line of Python and test code must fit the repository's black line length of 88 columns, which the pre-commit hook enforces. Wrap longer literals across several lines.

## Reliability
- `c = 0` gives finite values equal to `Sersic2D`.
- The exponent `2 + c` is used for both scaling and the outer root. The outer root must never be `1 / c`, because at `c = 0` that divides by zero and yields non-finite output.

## Usability
- The `c` sign convention is the only guide a user has to the isophote shape. The class docstring, the parameter description, and the predefined-models page must all state the same convention. A user who wants disky isophotes must pick negative `c`.
- A user can construct the model either with keywords or with the eight values in order, as with `Sersic2D`.

## Compatibility
- `Sersic2D` parameter names, order, defaults, and outputs are unchanged. Existing code that constructs `Sersic2D` is unaffected, and existing calls to the `Sersic2D` evaluation with seven inputs are unaffected.
- The new export is additive. No names are removed.

## Behavioral acceptance criteria
- With no arguments, `GeneralSersic2D` takes the `Sersic2D` defaults plus `c = 0`. Its values equal `Sersic2D` at the same parameters.
- For any parameters with `c = 0`, the output matches `Sersic2D` to floating-point tolerance.
- Positional construction with the eight values in order succeeds and binds each value to its parameter; the eighth positional argument binds to `c`.
- `c < 0` produces pointed, kite-like (disky) contours. `c > 0` produces squarish (boxy) contours.
- Reference example: amplitude 1, r_eff 25, n 4, x_0 50, y_0 50, ellip 0.5, theta -1, c 1.0. Evaluated at the x values [0.0, 1, 10, 100] paired with the y values [1, 100, 0.0, 10], the output matches the reference values [0.01711221, 0.10471922, 0.02426327, 0.1201565] within the test tolerance.
- Quantity case: amplitude 3 MJy/sr, x_0 1 arcsec, y_0 2 arcsec, r_eff 2 arcsec, n 4, c 1, ellip 0, theta 0. Evaluated at (3 arcsec, 2.5 arcsec), the result is 2.9704014001846475 MJy/sr within the test tolerance.
- The test modules import without error. Importing the example-models test module, and each other module that imports it, must succeed.

## Test requirements
- Import binding (required before the registry entry): the example-models test module must add `GeneralSersic2D` to its explicit import list from the functional models module, immediately after `Gaussian2D`. Its registry entry for the new model refers to the class by name when the module loads. If the name is not bound in that module, importing it raises a name error, which breaks every test module that imports it. Verify that the name is bound in the module before adding the registry entry.
- Register `GeneralSersic2D` in the 2D example-model table used by the generic model tests. Use the reference parameter tuple in the order given under Data model, the reference x values, y values, z values, the requires-scipy flag, and the limits. That fixture is constructed with the eight values as positional arguments, so the positional-construction requirement under API contracts must hold for it.
- Add a quantity-support entry in the quantity test module with the case above and bounding box disabled. Wrap its evaluation entry across several lines so that no line of the test module exceeds 88 columns.
- Add `GeneralSersic2D` to the scipy-dependent model set, and to each of the three non-finite fitting-exception lists in which `Sersic2D` appears: the LevMar list, the TRF list, and the DogBox list.
- Add `GeneralSersic2D` to the non-finite exception list for the LMLSQFitter (the list named NON_FINITE_LM_MODELS, which contains `Schechter1D`, `ExponentialCutoffPowerLaw1D`, and `BrokenPowerLaw1D`). Append it at the end of that list, as the reference does. This list does not contain `Sersic2D`, so it is not covered by the rule above and must be added explicitly.
- Existing `Sersic2D` test entries must remain unchanged and continue to pass.
