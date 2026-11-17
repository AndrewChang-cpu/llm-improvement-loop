"""Utilities for working with SHACL shapes graphs."""

from __future__ import annotations

from typing import Union

from rdflib.graph import Graph
from rdflib.namespace import RDF, SH
from rdflib.paths import AlternativePath, InvPath, MulPath, Path, SequencePath
from rdflib.term import Literal, Node, URIRef


class SHACLPathError(Exception):
    """Raised when a node does not form a valid SHACL path."""


# The implementation follows the SHACL-to-SPARQL path conversion in pyshacl.
def parse_shacl_path(
    shapes_graph: Graph,
    path_identifier: Node,
) -> Union[URIRef, Path]:
    """Convert the object of a ``sh:path`` triple into an RDFLib path.

    A valid SHACL path is either an IRI (a simple predicate, other than
    ``rdf:nil``), or a blank node that is an RDF list used as a sequence,
    carries ``sh:inversePath`` or ``sh:alternativePath``, or carries one of
    ``sh:zeroOrMorePath``, ``sh:oneOrMorePath`` or ``sh:zeroOrOnePath``.
    Sequences and alternatives must contain at least two items.

    :param shapes_graph: the Graph holding the shapes. It is only read,
        never modified.
    :param path_identifier: the path node, i.e. the object of the ``sh:path``
        triple. It is an IRI, a blank node, or a Literal.
    :return: the IRI itself as a URIRef for a simple path, otherwise a
        Path instance built from the core rdflib path classes.
    :raises TypeError: if ``path_identifier`` is a Literal.
    :raises SHACLPathError: if the node is not a valid SHACL path.
    """
    # A literal can never be a path.
    if isinstance(path_identifier, Literal):
        raise TypeError(
            f"Literals are not valid SHACL paths: {path_identifier!r}",
        )

    # Simple path: an IRI, except rdf:nil which denotes an empty list.
    if isinstance(path_identifier, URIRef):
        if path_identifier == RDF.nil:
            raise SHACLPathError("rdf:nil is not a valid SHACL path")
        return path_identifier

    # Sequence path: an RDF list.
    if shapes_graph.value(path_identifier, RDF.first) is not None:
        items = list(shapes_graph.items(path_identifier))
        if len(items) < 2:
            raise SHACLPathError(
                f"A sequence path needs at least two items: {path_identifier!r}"
            )
        return SequencePath(*[parse_shacl_path(shapes_graph, item) for item in items])

    # Inverse path: sh:inversePath
    inverse_value = shapes_graph.value(path_identifier, SH.inversePath)
    if inverse_value is not None:
        return InvPath(parse_shacl_path(shapes_graph, inverse_value))

    # Alternative path: sh:alternativePath, whose value is an RDF list.
    alternative_value = shapes_graph.value(path_identifier, SH.alternativePath)
    if alternative_value is not None:
        alternatives = list(shapes_graph.items(alternative_value))
        if len(alternatives) < 2:
            raise SHACLPathError(
                f"An alternative path needs at least two items: {path_identifier!r}"
            )
        return AlternativePath(
            *[parse_shacl_path(shapes_graph, item) for item in alternatives]
        )

    # Modifier paths: sh:zeroOrMorePath, sh:oneOrMorePath, sh:zeroOrOnePath.
    zero_or_more_value = shapes_graph.value(path_identifier, SH.zeroOrMorePath)
    if zero_or_more_value is not None:
        return MulPath(parse_shacl_path(shapes_graph, zero_or_more_value), "*")

    one_or_more_value = shapes_graph.value(path_identifier, SH.oneOrMorePath)
    if one_or_more_value is not None:
        return MulPath(parse_shacl_path(shapes_graph, one_or_more_value), "+")

    zero_or_one_value = shapes_graph.value(path_identifier, SH.zeroOrOnePath)
    if zero_or_one_value is not None:
        return MulPath(parse_shacl_path(shapes_graph, zero_or_one_value), "?")

    raise SHACLPathError(f"Unrecognized SHACL path node: {path_identifier!r}")
