[progress] The `total` we pass to a Progress renderable can now be `None`

## Type of changes

- [ ] Bug fix
- [x] New feature: https://github.com/Textualize/rich/issues/1054
- [ ] Documentation / docstrings
- [ ] Tests
- [ ] Other

## Checklist

- [x] I've run the latest [black](https://github.com/psf/black) with default args on new code.
- [x] I've updated CHANGELOG.md and CONTRIBUTORS.md where appropriate.
- [x] I've added tests for new code.
- [x] I accept that @willmcgugan may be pedantic in the code review.

## Description

With this PR we now render a "pulse" progress bar when the given `total` is None. 
Which is a new possibility we now have: this parameter used to be a `float`, and is now an `Optional[float]` - so it shouldn't bring any compatibility issues, as the type is just widened to a value that was not accepted according to the documentation, and which would raise exceptions before if it was used?

#### Design considerations

To carry the semantic of _"we don't know the 'total' value for my progress bar"_, instead of `None` we could have used other kinds of values, such as:
 - A negative value, like `total=-1`. The benefit would have been that the signature would still have been `float` , but the drawback is that the meaning of this value is less clear when debugging
 - A sentinel value, such as `total=rich.progress.UNDETERMINED` : probably the most explicit option, but a bit more cumbersome for our users than a good old `None`? :thinking: 

