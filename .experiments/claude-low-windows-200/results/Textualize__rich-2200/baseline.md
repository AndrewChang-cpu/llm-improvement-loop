Setting terminal window title

## Type of changes

- [ ] Bug fix
- [x] New feature
- [ ] Documentation / docstrings
- [ ] Tests
- [ ] Other

## Checklist

- [x] I've run the latest [black](https://github.com/psf/black) with default args on new code.
- [x] I've updated CHANGELOG.md and CONTRIBUTORS.md where appropriate.
- [x] I've added tests for new code.
- [x] I accept that @willmcgugan may be pedantic in the code review.

## Description

Adds support for setting the title of the terminal window.

There is no means within Rich of "resetting" the window title to its
previous value, meaning the title you set will persist even after your application
exists.

`fish` shell resets the window title before and after each command by default,
negating this issue. Windows Terminal and command prompt will also reset the title for you.
Most other shells and terminals, however, do not do this.

Some terminals may require configuration changes before you can set the title.
Some terminals may not support setting the title at all.

Other software (including the terminal itself, the shell, custom prompts, plugins, etc.)
may also set the terminal window title. This could result in whatever value you write
using this method being overwritten.


