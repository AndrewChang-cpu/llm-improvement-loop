Add API to support tracking progress while reading from a file

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

Hi Will! I've started using `rich` more and more, so far it's a great experience :wink: 

One of my common use case for the `rich.progress` module is tracking the progress made while reading from a file. In bioinformatics it's not rare to process gigabytes of files so I like to have an idea how long of a break I can take while processing my input data! 

![image](https://user-images.githubusercontent.com/8660647/146222942-19233138-9575-486e-845d-7312d3c6f627.png)

Manually updating the progress bar works for certain things, but for instance, when I want to pass a file-like handle to an API that consumes it (e.g `json.load`), there's no way to update the progress bar between each chunk. To do so, the only way I've found was to wrap the file-like object itself so that it updates the progress bar whenever the file is read from. This is something you could partially do with [`tqdm.tqdm.wrapattr`](https://tqdm.github.io/docs/tqdm/#wrapattr).

Since the `rich.progress` API has no straightforward support for this (like it does with `track` for an iterator), I made my own snippet for this, which ends up working well. I've been copying around in every project that uses `rich`, so I think it would make a good addition to the library!

## Changes

This PR adds the `rich.progress._Reader` class, which wraps a file-like object, and updates a `Progress` instance while being read from. The class itself is private; to get a reader, you have to use the new `Progress.read` method, which takes either a path or a file-like object, and returns a file reader with progress support.

This lets you do something like this (e.g. loading JSON-serialized data from a file, using `os.stat` to get the total number of bytes to be read):
```python
import json
from rich.progress import *

with Progress(columns=[BarColumn(), DownloadColumn()]) as progress:
    with progress.read("data.json") as f:
        data = json.load(f)
```

You can also directly pass a file-like object to `progress.read`, in which case you *must* specify the total:
```python
import json
from rich.progress import *

with Progress(columns=[BarColumn(), DownloadColumn()]) as progress:
    with open("data.json", "rb") as f:
        data = json.load(progress.read(f, total=2048))
```

In addition, I added a wrapper function `rich.progress.read` like `rich.progress.track` which handles setting up a progress, so that you can get a progress reader in just two lines:
```python
with rich.progress.read("data.json") as f:
    data = json.load(f)
```

### Notes

- In `rich.progress.read` and `Progress.read`, I made `total` an `int` instead of a `float`, because it should be a number of bytes so a float would not make sense here.
- If you `seek` the `_Reader`, it will also reset the position of the progress bar to the new position.






