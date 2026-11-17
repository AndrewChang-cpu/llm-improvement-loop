# Call from thread method

## Goals

- Provide a public method on the application object that lets code on a non-app thread (for example, a worker thread wrapping a third-party threaded API) run a callable in the app's context and receive its result, without managing the app's event loop.
- The call blocks the calling thread until the callable finishes, then returns its result or re-raises its exception. Exact propagation rules are in Workflows.
- Syntactic sugar and further convenience APIs are deferred.

## Scope

- In scope: one new public App method; the thread-entry state it needs; lifecycle bookkeeping in the run entry point; tests for the behaviours below.
- Out of scope: changes to widgets, the message pump, or drivers; new convenience wrappers; async-native alternatives.

## Assumptions

- The app's run entry point is the only place the event loop starts and stops, so thread-entry state must be owned there.

## Terminology

- App thread: the thread that calls the run entry point and on which the event loop runs.
- Calling thread: any other thread.
- Run entry point: the asynchronous coroutine, defined inside the App's synchronous run method, that awaits the App's async main. The event loop executes it. The synchronous run method creates and drives the loop and returns only after the loop finishes its teardown.
- App context: the framework's active-app context variable. Widget access through the app property resolves the app from it. It is per asyncio task, so it must be set inside the task that runs the callable.
- Invoke helper: the existing callback helper that calls a callable with at most as many positional arguments as it declares, and awaits the result if it is awaitable.
- Scheduled result: the blocking result handle returned by asyncio's threadsafe scheduling of a coroutine onto a loop. It is the only object the calling thread waits on.

## Workflows

The method checks these conditions in order:

1. If the app is not running (no loop recorded), raise a runtime error with the message "App is not running". This applies before the app starts and after it stops.
2. If the calling thread is the app thread, raise a runtime error whose message states the call must run in a different thread from the app.
3. Otherwise, schedule work onto the app's loop thread-safely. The scheduled work must:
   a. Make the app the active app in the app context, using the App's existing active-app helper, before the callable runs.
   b. Bind all supplied positional and keyword arguments to the callable first, so the invoke helper receives a callable needing no arguments. The invoke helper then calls it and awaits the result if awaitable. Do not pass the forwarded positional arguments to the invoke helper directly, because it truncates them to the callable's declared parameter count.
4. The calling thread makes one blocking wait on the scheduled result, then returns the value it yields. Completion is signalled only by that scheduled result.
5. If the callable raises, the exception reaches the calling thread through the scheduled result and is re-raised there. The method must not catch, retry, wrap, or otherwise handle it. Identity is not guaranteed: asyncio's cross-thread bridge re-creates an exception whose type is exactly the concurrent.futures cancellation, timeout, or invalid-state class as the matching asyncio class, with the same arguments. Other exception types arrive as the same object. Accept this conversion; do not add code to undo it.
6. Callables that touch widgets through the app (for example, querying and writing to one) must succeed when called this way.

Lifecycle: when the app starts running, the run entry point records the event loop and the app thread's identifier before awaiting the App's async main. It awaits that main inside a try/finally and clears both records in the finally clause, so they are cleared as soon as the async main returns or raises, for any reason. Clearing must happen inside the run entry point, not in the synchronous run method after loop teardown; otherwise a call during teardown could be scheduled onto a loop that never runs it and wait forever. Once cleared, later calls follow step 1.

## Data model

- The App holds two thread-entry values: a reference to the event loop, and an integer identifier of the app thread.
- Cleared state: the loop reference is empty (no value); the thread identifier is the integer zero.
- Both are cleared when the App is constructed, so a call before run is detected as not running.
- Both are set at the start of the run entry point, from the thread that invokes run, before the async main is awaited.
- Both are cleared in a finally clause wrapping the await of the async main. A finished app is never reported as running once its async main ends, and clearing happens before loop teardown begins.

## API contracts

- A public method named call_from_thread on the App class.
- Input: a required callable that returns a value or an awaitable of a value, followed by any number of positional and keyword arguments. Every supplied argument is forwarded unchanged, regardless of how many parameters the callable declares, including variadic callables. If the callable cannot accept the arguments, its own error propagates.
- Return: the callable's result, after awaiting if needed. Use a dedicated type variable for this result, separate from the App's existing type variable(s) for its exit or return value. Annotate the callable parameter as returning that type or an awaitable of it, and annotate the method's return with the same type variable. No untyped return.
- Raises a runtime error when the app is not running or when called from the app thread (see Error handling). Callable exceptions are re-raised on the calling thread under Workflows step 5.

## Module architecture

- The method belongs on the App class in the app module, grouped with other App-level methods. It must not be placed in the message pump, widgets, or drivers.
- The thread-entry values belong to the App and are initialized in its constructor.
- Setting and clearing them belongs in the run entry point (the coroutine awaiting the async main). Not in the synchronous run method, whose cleanup runs after loop teardown, and not in message processing.
- Reuse existing mechanisms: the App's active-app helper, the invoke helper from the callback module, and standard threadsafe coroutine scheduling onto a given loop.

## Implementation constraints

- Calls to the callable must go through the existing invoke helper. Do not reimplement awaitable handling or argument invocation, and do not add a parallel callback-invocation path.
- Set the active app inside the scheduled work, before the callable is invoked. Setting it on the calling thread has no effect on the scheduled work.
- The not-running check must rely on the cleared state, not a separate flag.
- Bind positional arguments to the callable before using the invoke helper (see Workflows 3b).
- Read the outcome (value or exception) only from the scheduled result (see Workflows 4 and 5). Do not capture the outcome inside the scheduled work, wrap the callable in a result-carrying tuple or a separate future, or catch exceptions around the scheduled work. Such custom capture is not required and diverges from the reference.
- Do not add a polling loop, timed retries, or periodic state re-checks around the wait (see Reliability).

## Dependencies

- No new third-party dependencies.
- Use only standard-library modules: threading, asyncio, the future type from concurrent.futures, and functools partial binding, plus the existing invoke helper and active-app variable. Imports the app module already has or can add from the standard library are acceptable.

## Error handling

- Not running: runtime error with the exact message "App is not running".
- Same thread: runtime error with the exact message "The `call_from_thread` method must run in a different thread from the app". It must not describe the not-running case.
- Callable exceptions are not swallowed, wrapped, retried, or treated specially because of their type. This includes timeout exceptions on some Python versions. Asyncio's re-creation of exact concurrent.futures types (Workflows 5) is expected, not an error to handle.
- Shutdown: calls after shutdown are rejected by the entry check and never block. Do not add a mechanism that watches loop state during the wait.

## Naming

- Test functions in the new module must have names that describe exactly what each verifies. Comments must match the code they describe (for example, the exit value a test uses). Misspelled or stale names and comments are not acceptable.

## Documentation

- The docstring must state that Textual objects are not thread-safe, that the call ensures the code runs in the correct context, and that the call blocks until the callable returns.
- The Args section must describe the callable and the forwarded arguments.
- The Raises section must document both runtime error cases: the app not running (including after it has stopped) and a call from the app thread.

## Reliability

- The method blocks only until the scheduled callable completes, using a single blocking wait on the scheduled result, not timed waits in a loop.
- Thread-entry state is cleared on every exit path of the run entry point, including exceptions, and before loop teardown begins, so no call after shutdown is scheduled onto a loop that will never run it.

## Maintainability

- New standard-library imports go in the module's existing import block, in its existing sorted order, not appended or inserted out of order.

## Compatibility

- The project declares Python 3.7 and later. The returned value, the two runtime errors, exception propagation, and no blocking after shutdown must hold on every supported version.
- A timeout-class exception's class on the calling thread depends on the interpreter's asyncio (Workflows 5). Do not normalize it in the implementation, and do not require one specific class in tests.
- Use only APIs available on the minimum supported version. Do not use asyncio.to_thread in the implementation or tests.
- Any new module, including tests, must import on the minimum version. Builtin generic annotations evaluated at import time (for example, tuple or list subscripts in a module-level signature) require the future-annotations import at the top of the module or equivalent typing names. Follow the repository convention of starting modules with that import when they use such annotations.

## Behavioral acceptance criteria

- A background thread calling the method with a callable that writes to a text log widget in the app causes the write to occur and the method to return.
- A callable that returns an awaitable is awaited, and its result is returned to the calling thread.
- A callable raising a timeout-class exception (for example, from a third-party timeout) causes an exception with the same message and arguments on the calling thread, and the call returns instead of hanging. The class may be the asyncio-converted one (Workflows 5).
- A variadic callable receives all supplied positional arguments, and a callable with named parameters receives the supplied keyword arguments.
- A call from the app thread raises a runtime error.
- A call before the app runs raises the "App is not running" runtime error.
- A call made after the app's run has returned raises the "App is not running" runtime error and does not block.
- A background thread that exits the app through the method causes run to return the supplied exit value.

## Test requirements

- Place the tests in a concurrency-focused test module under the tests directory, following the repository's naming convention.
- Drive the app with a headless run from the test's main thread. Start the background calling thread from the app's ready hook (or after mount), so cross-thread calls happen while the app is running.
- Background threads must be daemon threads so they cannot keep the process alive. After run returns, join each with a bounded wait and assert it has finished; a thread still alive is a failure.
- Every cross-thread call must be issued while the app is running, and its outcome checked. Do not issue a final call from a cleanup path that can run after the app stops.
- The test run must terminate by itself. A process that hangs after its tests pass counts as failing.
- Test code must not create, start, or drive its own event loop, or use APIs unavailable on the minimum Python version.
- Tests must not read private App attributes (loop or thread-identifier state). Verify through public results: the callable's return value, the value run returns, and raised exceptions.
- For exception propagation, assert that an exception with the expected message and arguments is raised on the calling thread and the call returns. Do not assert object identity or the exact concurrent.futures class of a timeout-class exception, and do not write tests whose result depends on whether the builtin and concurrent.futures timeout errors are the same type.
- The widget-access test must not assert rendered or layout-dependent widget state (for example, line counts after a write), because widgets may not be laid out yet. Verify the callable completes without error and the app exits with a supplied code.
- Every test in the new module must pass on the recorded Python environment before the work is considered done.
- Cover: the not-running case, the same-thread case, widget access from the callable, an awaitable callable, exception propagation (including a timeout-class exception), argument forwarding to a variadic callable, and a call after the app has stopped.
