Concise Bounded Description

This PR implements a Graph() function cbd() for 'Concise Bounded Description'. It extracts a subgraph from a source graph as per the rules in the W3C member submission [1].

This PR includes documentation for the method, tests and I want it mostly to be an example of a well-presented PR, not so much a rocket science improvement to the codebase!

It is also a precursor to implementing SPARQL's `DESCRIBE` queries though.

~Please note this PR adds `black` to requirements.txt as I'd like `black` to be run on all code being submitted to rdfllib and, for rdflib 6.0.0, all existing code too.~

[1] https://www.w3.org/Submission/CBD/
