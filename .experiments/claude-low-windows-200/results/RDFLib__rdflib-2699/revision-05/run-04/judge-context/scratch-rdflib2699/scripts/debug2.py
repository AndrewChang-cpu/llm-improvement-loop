import sys
T = sys.argv[1]; sys.path.insert(0, T)
import rdflib
from rdflib import Graph, BNode, URIRef
from rdflib.namespace import SH
from rdflib.extras import shacl as cand
assert rdflib.__file__.startswith(T), rdflib.__file__
P1, P2 = URIRef("http://example.org/p1"), URIRef("http://example.org/p2")
g = Graph(); b = BNode()
g.add((b, SH.inversePath, P1)); g.add((b, SH.zeroOrMorePath, P2))
print("triples on node:", sorted(str(p) for p in g.predicates(b)))
try:
    print("cand:", repr(cand.parse_shacl_path(g, b)))
except Exception as e:
    print("cand raised", type(e).__name__, e)
