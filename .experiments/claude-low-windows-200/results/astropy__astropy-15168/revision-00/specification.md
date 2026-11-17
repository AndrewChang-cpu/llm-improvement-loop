Cosmo parameters properties

I've added 2 properties to `Cosmology`:
1. `parameters` : an immutable dictionary of the non-derived ``Parameter``s defined on `Cosmology`. When accessed from the class the values are the Parameter objects. When accessed from the cosmology instance the values are the Parameter values on the cosmology instance.
2. `derived_parameters` : the same, but for the derived parameters, e.g `Ode0` in flat cosmologies.

The idea is that when `Cosmology` is a dataclass you eventually won't be able to do `Cosmology.H0` to get the `Parameter` object. But it will be still be easy to access the `Parameter` object as `Cosmology.parameters["H0"]`.
For v6.0 I do not plan to remove direct access to `Cosmology.H0`, etc. This will either be deprecated in a future version or will be supported through Python's [dataclass_transform](https://peps.python.org/pep-0681/) mechanism. Pros and cons to both.


Please do NOT squash.
