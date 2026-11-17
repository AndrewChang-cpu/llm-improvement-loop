Add TimeDelta format `quantity_str` for Year Day Hour Minute Sec string

<!-- This comments are hidden when you submit the pull request,
so you do not need to remove them! -->

<!-- Please be sure to check out our contributing guidelines,
https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md .
Please be sure to check out our code of conduct,
https://github.com/astropy/astropy/blob/main/CODE_OF_CONDUCT.md . -->

<!-- If you are new or need to be re-acquainted with Astropy
contributing workflow, please see
http://docs.astropy.org/en/latest/development/workflow/development_workflow.html .
There is even a practical example at
https://docs.astropy.org/en/latest/development/workflow/git_edit_workflow_examples.html#astropy-fix-example . -->

<!-- Please just have a quick search on GitHub to see if a similar
pull request has already been posted.
We have old closed pull requests that might provide useful code or ideas
that directly tie in with your pull request. -->

<!-- We have several automatic features that run when a pull request is open.
They can appear daunting but do not worry because maintainers will help
you navigate them, if necessary. -->

### Description
<!-- Provide a general description of what your pull request does.
Complete the following sentence and add relevant details as you see fit. -->

<!-- In addition please ensure that the pull request title is descriptive
and allows maintainers to infer the applicable subpackage(s). -->

<!-- READ THIS FOR MANUAL BACKPORT FROM A MAINTAINER:
Apply "skip-basebranch-check" label **before** you open the PR! -->

This pull request adds a new string `TimeDelta` format `"quantity_str"` that represents the time delta as a string with one or more Quantity components. This format provides a human-readable multi-scale string representation of a time delta. It is convenient for applications like a configuration file or a command line option. It is NOT intended for high-precision applications since the internal  calculations are done using 64-bit floating point numbers.

The driver for this is that it can be convenient to have a human-readable string representing a time delta which has natural scales so that delta from seconds to years are manageable. A string representation is useful in configuration files and application command line inputs.

This PR defines a new format which is like `"[-+]? 1yr 2d 3hr 4min 5.6s"`. The format is specified as follows:
- The string is a sequence of one or more components.
- Each component is a number (float or int) followed by an astropy unit of time.
- For input, whitespace within the string is allowed but optional.
- For output, there is a single space between components.
- The allowed components are listed below.
- The order (yr, d, hr, min, s) is fixed but individual components are optional.

The allowed component units are shown below:
- "yr": years (365.25 days)
- "d": days (24 hours)
- "hr": hours (60 minutes)
- "min": minutes (60 seconds)
- "s": seconds

These definitions correspond to physical units of time and are NOT calendar date intervals. Thus adding "1yr" to "2000-01-01 00:00:00" will give "2000-12-31 06:00:00" instead of "2001-01-01 00:00:00".

The format is defined internally as a single regular expression that could be used in other non-Python implementations for parsing.

#### Output subformats

The `quantity_str` format supports output sub-formats `"multi", "yr", "d", "hr", "min", "s"` to allow specifying the string output as a single unit or in the default multi-unit format. 

The `precision` attribute (default=3) applies to the specified subformat. For example `TimeDelta("100.0d 1.0123456789012345s", precision=9, out_subfmt="d").value` is `"100.000011717d"`.

#### Why not re-use an existing standard?

The only other existing standard that I am aware of for time intervals is defined in [ISO 8601 durations](https://en.wikipedia.org/wiki/ISO_8601#Durations) that represent the duration between two dates. The ISO 8601 duration format is: P(n)Y(n)M(n)DT(n)H(n)M(n)S. The fundamental problem with this format is that it explicitly depends on the reference start date as a calendar date in Year Month day hour min sec. So this is not suitable for physical time deltas that are independent of the reference date.

<!-- If the pull request closes any open issues you can add this.
If you replace <Issue Number> with a number, GitHub will automatically link it.
If this pull request is unrelated to any issues, please remove
the following line. -->

<!-- Optional opt-out -->

- [ ] By checking this box, the PR author has requested that maintainers do **NOT** use the "Squash and Merge" button. Maintainers should respect this when possible; however, the final decision is at the discretion of the maintainer that merges the PR.
