Adding Namespace.__contains__()

No issue for this, just a quick addition for usability/literacy while working with the library.

## Proposed Changes

  - Adds a `Namespace.__contains__()` method to enable syntax sugar of `ref in ns`. This is a natural way to discover if an arbitrary `URIRef` is in the `Namespace`.
  - Current method would be manually writing `ref.startswith(ns)`, which doesn't preserve semantics

This has possible extension to `NamespaceManager`, testing if a `URIRef` is in any managed namespace.

```
class NamespaceManager():
    def __contians__(self, ref):
        return any(ref.startswith(ns) for x, ns in self.namespaces())
```

Note that in `NamespaceManager`, namespaces are stored as `URIRef`s, not `Namespace` objects :/

Hoping this starts a discussion about some usability concerns.
