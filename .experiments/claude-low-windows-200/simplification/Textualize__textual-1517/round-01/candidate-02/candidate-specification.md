# Call from thread method

## Goals

- Provide a public method on the application object that lets code on a non-app thread (for example, a worker thread wrapping a third-party threaded API) run a callable in the app's context and receive its result. Integrators should not manage the app's event loop themselves.
- The call blocks the calling thread until the callable finishes, then returns its result or re-raises its exception. Propagation rules are in Workflows.
- This is a step toward an integration answer for third-party APIs. Syntactic sugar and further convenience APIs are deferred.

## Scope

- In scope: one new public App method; the thread-entry state it needs; lifecycle bookkeeping in the run entry point; tests for the behaviours below.
- Out of scope: changes to widgets, the message pump, or drivers; new convenience wrappers; async-native alternatives.

## Assumptions

- The app's run entry point is the only place the event loop starts and stops, so thread-entry state is owned there.

## Terminology

- App thread: the thread that calls the app's run entry point and on which the event loop runs.
- Calling thread: any other thread.
- Run entry point: the asynchronous coroutine, defined inside the App's synchronous run method, that awaits the App's async main. The synchronous run method creates and drives the loop and returns only after the loop's own teardown.
- App context: the framework's active-app context variable. Widget access through the app property resolves the app from it. It is per asyncio task, so it must be set inside the task that runs the callable.
- Invoke helper: the existing callback helper that calls a callable with at most as many positional arguments as it declares, and awaits the result if awaitable.
- Scheduled result: the blocking result handle returned when a coroutine is scheduled onto the app's loop thread-safely. The calling thread waits only on this object.

## Workflows

The method checks these conditions in order:

1. If no event loop is recorded (app not yet started, not running, or already stopped), raise a runtime error with the message "App is not running".
2. If the calling thread is the app thread, raise a runtime error whose message says the call must run in a different thread from the app.
3. Otherwise, schedule work onto the app's loop thread-safely. The scheduled work must:
   a. Set the app as the active app in the app context, using the App's existing active-app helper, before the callable runs.
   b. Bind all supplied positional and keyword arguments to the callable first, producing a callable that needs no arguments. Pass that to the invoke helper, which calls it and awaits the result if awaitable. Do not pass forwarded positional arguments to the invoke helper directly, because it truncates them to the callable's declared parameter count.
4. The calling thread performs one blocking wait on the scheduled result and returns the value it yields. Completion is signalled only by that result.
5. If the callable raises, the exception reaches the calling thread through the scheduled result and is re-raised there without handling. Asyncio's cross-thread bridge re-creates an exception whose type is exactly the concurrent.futures cancellation, timeout, or invalid-state class as the matching asyncio class, with the same arguments. Other types arrive as the same object. Accept this conversion; do not add code to undo it.
6. Callables that touch widgets through the app (for example, querying and writing to a widget) must succeed when called this way.

Lifecycle: the run entry point records the event loop and the app thread's identifier when the app starts, before awaiting the async main. It awaits the async main inside try/finally and clears both records in the finally clause, so they are cleared as soon as the async main returns or raises, for any reason. Clearing must happen inside the run entry point, not in the synchronous run method after loop teardown; otherwise a call during teardown could be scheduled onto a loop that never runs it and wait forever. Later calls then follow step 1.

## Data model

- The App holds two thread-entry values: a reference to the app's event loop, and an integer identifier of the app thread.
- Cleared state: the loop reference is empty; the thread identifier is the integer zero, not an empty value.
- Both are in cleared state when the App is constructed, so a call before run is detected as not running.
- Both are set at the start of the run entry point, from the thread invoking run, before the async main is awaited. They are cleared in the finally clause around that await, so a finished app is never reported as running after its async main ends.

## API contracts

- A public method named call_from_thread on the App class.
- Input: a required callable that returns a value or an awaitable of a value, followed by any number of positional and keyword arguments. Every supplied argument is forwarded unchanged, including to variadic callables. If the callable cannot accept them, its own error propagates.
- Return: the callable's result, after awaiting if needed. Use a dedicated type variable for the result, separate from the App's existing type variable(s) for exit or return values. Annotate the callable as returning that type or an awaitable of it, and annotate the return with the same variable. No untyped return.
- Raises a runtime error when not running or called from the app thread (see Error handling). Callable exceptions are re-raised per Workflows step 5.

## Module architecture

- The method belongs on the App class in the app module, grouped with other App-level methods, not in the message pump, widgets, or drivers.
- The thread-entry values belong to the App and are initialized in its constructor.
- Setting and clearing them belongs in the run entry point only: not in the synchronous run method, whose cleanup runs after loop teardown, and not in message processing.
- Reuse existing mechanisms: the App's active-app helper, the invoke helper from the callback module, and standard threadsafe scheduling of a coroutine onto a given loop.

## Implementation constraints

- Calls to the callable go through the existing invoke helper. Do not reimplement awaitable handling or argument invocation, and do not add a parallel callback-invocation path.
- Set the active app inside the scheduled work. Setting it on the calling thread has no effect there.
- The not-running check relies on the cleared state, not a separate flag.
- Bind positional arguments before the invoke helper is used (Workflows 3b).
- Do not capture the outcome inside the scheduled work: no result-carrying tuple, separate future, or exception catching around it. The outcome is read only from the scheduled result. Custom capture is not required and diverges from the reference.
- No polling loop, timed retries, or periodic state re-checks around the wait.

## Dependencies

- No new third-party dependencies.
- Only standard-library modules: threading, asyncio, the future type from concurrent.futures, and functools partial binding, plus the existing invoke helper and active-app variable.

## Error handling

- Not running: runtime error with the exact message "App is not running".
- Same thread: runtime error with the exact message "The `call_from_thread` method must run in a different thread from the app". It must not describe the not-running case.
- Callable exceptions are not swallowed, wrapped, retried, or treated specially by type, including timeout exceptions on some Python versions. The asyncio class conversion (Workflows 5) is expected, not an error.
- After shutdown, calls are rejected by the not-running check at entry and never block. Do not add a mechanism that watches loop state during the wait.

## Naming

- Test function names must state exactly what each test verifies. Test comments must match the code they describe, including exit values used. Misspelled or stale names and comments are not acceptable.

## Documentation

- The docstring states that Textual objects are not thread-safe, that the call ensures the code runs in the correct context, and that the call blocks until the callable returns.
- The Args section describes the callable and the forwarded arguments.
- The Raises section documents both runtime errors: app not running (including after it stopped) and call from the app thread.

## Reliability

- Block only until the scheduled callable completes, using a single blocking wait on the scheduled result, not timed waits in a loop.
- Thread-entry state is cleared on every exit path of the run entry point, including exceptions, before loop teardown begins.

## Maintainability

- New standard-library imports go in the module's existing import block in sorted order, not appended or inserted out of order.

## Compatibility

- The project declares Python 3.7 and later. Required outcomes must hold on every supported version: returned value, both runtime errors, exception propagation, and no blocking after shutdown.
- The timeout-class exception's class on the calling thread depends on the running interpreter's asyncio (Workflows 5). Do not normalize it, and do not require one specific class in tests.
- Use only APIs available on the minimum version; for example, not asyncio.to_thread in implementation or tests.
- New modules, including tests, must import on the minimum version. Builtin generic annotations evaluated at import time (for example, tuple or list subscripts in module-level signatures) require the future-annotations import at the top of the module, following the repository convention.

## Behavioral acceptance criteria

- A background thread calling the method with a callable that writes to a text log widget in the app causes the write to occur and the method to return.
- A callable returning an awaitable is awaited, and its result is returned to the calling thread.
- A callable raising a timeout-class exception (for example, from a third-party timeout) causes an exception with the same message and arguments on the calling thread, and the call returns instead of hanging. The class may be the asyncio-converted one.
- A variadic callable receives all supplied positional arguments, and a callable with named parameters receives the supplied keyword arguments.
- A call from the app thread raises a runtime error.
- A call before the app runs raises "App is not running".
- A call after run has returned raises "App is not running" and does not block.
- A background thread that calls the app's exit through the method causes run to return the supplied exit value.

## Test requirements

- Place the tests in a concurrency-focused test module under the tests directory, following the repository naming convention.
- Drive the app with a headless run from the main thread. Start background calling threads from the app's ready hook (or after mount) so cross-thread calls happen while the app runs.
- Background threads must be daemon threads. After run returns, join each with a bounded wait and assert it finished; a live thread is a failure.
- Every cross-thread call must be issued while the app runs, and its outcome checked. Do not issue final calls from a cleanup path that can run after the app stops.
- The test run must terminate by itself; a hang after success is a failing check.
- Tests must not create, start, or drive their own event loop, or use APIs unavailable on the minimum supported version.
- Tests must not read private App attributes. Verify through public results: the callable's return value, the value run returns, and raised exceptions.
- For exception propagation, assert that an exception with the expected message and arguments is raised on the calling thread and the call returns. Do not assert object identity or the exact concurrent.futures class of a timeout-class exception, and do not make pass or fail depend on whether the builtin and concurrent.futures timeout errors are the same type.
- The widget-access test must not assert rendered or layout-dependent state (such as line counts). Verify that the callable completes without error and the app exits with a supplied code.
- Every test in the new module must pass on the recorded Python environment.
- Cover: the not-running case, the same-thread case, widget access, an awaitable callable, exception propagation including a timeout-class exception, variadic argument forwarding, and a call after the app has stopped.
