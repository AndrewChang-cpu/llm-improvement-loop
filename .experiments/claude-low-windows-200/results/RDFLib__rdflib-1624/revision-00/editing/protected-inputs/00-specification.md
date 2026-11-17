Feature prepareupdate

Fixes #272
Slightly speculative, other option is close #272 with `wontfix`

## Proposed Changes
Basically, follow the pattern established in `prepareQuery`

  - Create an Update class
  - Add a `prepareUpdate` to `processor.py`
  - Propagate pattern
  - Add test.

