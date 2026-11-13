Add py:type directive and role for documenting type aliases

### Feature or Bugfix
- Feature

### Purpose
This pull request adds a `py:type` directive for documenting type aliases (https://typing.readthedocs.io/en/latest/spec/aliases.html#type-aliases), and a `py:type` role for linking to them.

```rst
.. py:type:: Alias1
   :value: list[str | int]

   This is my type alias.

:py:type:`Alias1` is my type alias.
```

### Detail
- I've chosen to make a new directive for documenting type aliases, rather than add a new option to the `data` or `attribute` directives, because not all of the options on the `data` and `attribute` directives apply to a type alias (eg. `type`). In addition, type aliases seem to be classified differently from variable assignments by Python. Python documentation treats type aliases almost like first class citizens.
  - Documenting with a new directive means that if a user is currently using `type` in their code, but they're documenting it using the workaround of documenting it as an assignment (eg. `.. py:data:: Url\n   :type: TypeAlias\n   :value: str`), the user will likely want to update their documentation to use this new directive. I'm assuming that the number of users using `type` in their code is quite low, and therefore this trade off seemed worth it.
- I've chosen to name the directive and role "type" because that's also the keyword used to define a type alias in Python. I considered using "typealias", "alias", or some thing similar, but it seemed safer to choose the same word used in Python syntax because CPython may change the usage of the `type` keyword in the future to define more than just type aliases.
  - This overlaps with the `:type:` field, which potentially makes understanding rST syntax more confusing for users who are learning rST for the first time. But this trade-off seemed worth it.
- I've chosen to have users specify the type being aliased in a `:value:` option, rather than in the signature (eg. `.. py:type:: MyAlias = int`), because this is consistent with how the `data` and `attribute` directives work. So I think it makes the syntax more intuitive for users.
- I've chosen to make specifying a value of the alias optional because there could be cases where a user wants to declare the alias, but not make the type that is aliased public. For example:
  ```python
  type MyAlias = str

  def generate() -> MyAlias:
      ...
  def accept(arg: MyAlias) -> None:
     ...

  # To be used like the following:
  accept(generate())
  ```

  In the above example, a user may want to allow users to pass this type between parts of the API, without letting the user do anything else with instance of `MyAlias`, by not documenting what `MyAlias` is aliased from. So the user would document this as follows:

  ```rst
  .. py:type:: MyAlias

  .. py:function:: generate() -> MyAlias

  .. py:function:: accept(arg: MyAlias) -> None
  ```

  Users can currently do something similar with classes, where they might define a class but not document any of the attributes on it.

  ```rst
  .. py:class:: MyClass

  .. py:function:: generate() -> MyClass

  .. py:function:: accept(arg: MyClass) -> None
  ```

- I've chosen to name the option "value" because this is consistent with the `data` and `attribute` directives. In addition, this is the terminology used in `typing.TypeAliasType` and in the ast node.

  ```pycon
  >>> import ast
  >>> class A:
  ...     type MyAlias = int
  ...
  >>> type(A.MyAlias)
  <class 'typing.TypeAliasType'>
  >>> A.MyAlias.__value__  # Note the attribute name "__value__"
  <class 'int'>
  >>> m = ast.parse("type PuzzleInput = list[tuple[list[str], int]]")
  >>> m.body[0].value  # Note the attribute name "value"
  <ast.Subscript object at 0x7dd5ba91afd0>
  ```

### Relates
- Closes #7896


