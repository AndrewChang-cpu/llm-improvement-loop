Endpoint resolution v2: builtin parameter values

This PR is part of the ongoing endpoint resolution v2 work, together with #2737, #2740, #2751, #2747. It contains the code that assigns values to a list of "builtin parameters" that may be referenced by endpoint rulesets. It's glue code between the existing `ClientCreator` and `ClientArgsCreator` and the future `EndpointProvider` (see #2737).

Q: By itself, this PR adds only unused code. Why is it a separate PR? — A: I decided to break this out of a larger PR with all the middleware for calling `EndpointProvider` to keep this a separate review/discussion. Even though the code is pretty simple, there could be a complex discussion hiding behind each parameter assignment and how it is tested. Let's get these debates out of the way first :) 