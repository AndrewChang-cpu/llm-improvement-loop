import sys, importlib.util
T = sys.argv[1]; sys.path.insert(0, T)
import rdflib
from rdflib import Graph, BNode, Literal, URIRef
from rdflib.namespace import SH, XSD
from rdflib.extras import shacl as cand
assert rdflib.__file__.startswith(T)
spec = importlib.util.spec_from_file_location("ref_shacl", sys.argv[2])
ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
assert ref.__file__ == sys.argv[2]
P1, P2 = URIRef("http://example.org/p1"), URIRef("http://example.org/p2")
def run(mod, triples):
    g = Graph(); b = BNode()
    for p, o in triples(b): g.add((b, p, o))
    try:
        return f"OK {mod.parse_shacl_path(g, b)!r}"
    except Exception as e:
        return type(e).__name__
cases = {
 "inverse+zeroOrMore on one node": lambda b: [(SH.inversePath, P1), (SH.zeroOrMorePath, P2)],
 "inverse -> Literal('')": lambda b: [(SH.inversePath, Literal(""))],
 "inverse -> Literal('0', xsd:integer)": lambda b: [(SH.inversePath, Literal("0", datatype=XSD.integer))],
 "inverse -> Literal('x')": lambda b: [(SH.inversePath, Literal("x"))],
 "zeroOrMore -> Literal('')": lambda b: [(SH.zeroOrMorePath, Literal(""))],
 "inverse -> URIRef('')": lambda b: [(SH.inversePath, URIRef(""))],
}
for name, t in cases.items():
    r, c = run(ref, t), run(cand, t)
    print(("SAME" if r == c else "DIFF"), name, "| ref:", r, "| cand:", c)
