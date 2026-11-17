# Call from thread method

## Goals

- Provide a public method on the application object that lets code running on a non-app thread (for example, a worker thread wrapping a third-party threaded API) run a callable in the app's context and receive its result. Integrators should not have to manage the app's event loop themselves.
- Keep behaviour predictable: the call blocks the calling thread until the callable has finished, then returns its result, or re-raises the exception the callable raised. The exact propagation rules are in Workflows.
- This is a step toward an integration answer for third-party APIs. Syntactic sugar and further convenience APIs are deferred.

## Scope

- In scope: one new public method on the App class; the thread-entry state the method needs; lifecycle bookkeeping in the app's run entry point; and tests for the behaviours listed below.
- Out of scope: changes to widgets, the message pump, or drivers; new convenience wrappers; async-native alternatives.

## Assumptions

- The app's run entry point is the only place the app's event loop starts and stops. Thread-entry state must therefore be owned there.

## Terminology

- App thread: the thread that calls the app's run entry point and on which the app's event loop runs.
- Calling thread: any thread other than the app thread.
- Run entry point: the asynchronous coroutine, defined within the App's synchronous run method, that awaits the App's async main. It is the coroutine that the event loop executes. It is distinct from the synchronous run method, which creates and drives the loop and returns only after the loop has finished its own teardown.
- App context: the framework's active-app context variable. Framework code such as widget access through the app property resolves the app from it, and it is per asyncio task, so it must be established inside the task that runs the callable.
- Invoke helper: the existing callback helper that calls a callable with at most as many positional arguments as the callable declares, and awaits the result if it is awaitable.
- Scheduled result: the blocking result handle returned by asyncio's threadsafe scheduling of a coroutine onto the app's event loop. It is the only object the calling thread waits on.

## Workflows

The method must check the following conditions in this order:

1. If the app is not running (no event loop has been recorded), raise a runtime error with the message "App is not running". This applies before the app has started and after it has stopped.
2. If the calling thread is the app thread, raise a runtime error whose message states that the call must run in a different thread from the app.
3. Otherwise, schedule work onto the app's event loop in a thread-safe way. The scheduled work must:
   a. Make the app the active app in the app context for that task, using the App's existing active-app helper, before the callable runs.
   b. Bind every supplied positional argument and every supplied keyword argument to the callable first, so that the callable is handed to the invoke helper as a callable that needs no positional arguments from the invoke helper. The invoke helper then calls it and awaits the result when it is awaitable. Do not pass the forwarded positional arguments to the invoke helper as separate values, because the helper truncates them to the callable's declared parameter count.
4. The calling thread waits for the scheduled work to complete with one blocking wait on the scheduled result, then returns the value that the scheduled result yields. Completion is signalled only by that scheduled result.
5. If the callable raises, the exception reaches the calling thread through the scheduled result and is re-raised there. The method must not catch, retry, wrap, or otherwise handle it. Exception identity is not guaranteed: asyncio's cross-thread bridge re-creates an exception whose type is exactly the concurrent.futures cancellation, timeout, or invalid-state class as the matching asyncio class, carrying the same arguments. Exceptions of any other type arrive as the same object. Accept this conversion as the expected behaviour; do not add code to undo it.
6. Callables that touch widgets through the app (for example, querying a widget and writing to it) must succeed when called this way.

Lifecycle: the app's run entry point records the event loop and the app thread's identifier when the app starts running, before it awaits the App's async main. It awaits that async main inside a try/finally construct and clears both records in the finally clause, so they are cleared as soon as the async main returns or raises, for any reason including an error. This clearing must happen inside the run entry point, not in the synchronous run method after the event loop has torn down; otherwise a call made during that teardown window can be scheduled onto a loop that will never run it and would then wait forever. Once cleared, later calls follow step 1 and raise instead of waiting.

## Data model

- The App holds two thread-entry values: a reference to the app's event loop, and an integer identifier of the app thread.
- The loop reference is empty (no value) when cleared. The thread identifier's cleared value is the integer zero, not an empty value.
- Both are in their cleared state when the App is constructed, so a call made before run is detected as not running.
- Both are set at the start of the run entry point, from the thread that invokes run, before the App's async main is awaited.
- Both are cleared in a finally clause that wraps the await of the App's async main inside the run entry point. A finished app is never reported as running from the moment its async main ends, and the clearing happens before the event loop begins its teardown.

## API contracts

- A public method named call_from_thread on the App class.
- Input: a required callable that may return a value or an awaitable of a value; followed by any number of positional arguments and any keyword arguments. Every supplied argument is forwarded to the callable unchanged, regardless of how many parameters the callable declares, including variadic callables. If the callable cannot accept the arguments, its own error propagates.
- Return: the callable's result, after awaiting if needed. Use a dedicated type variable for the callable's result, separate from the App's existing type variable(s) used for its exit or return value. Annotate the callable parameter as a callable returning either that type or an awaitable of it, and annotate the method's return with the same dedicated type variable. Do not use an untyped return.
- Raises a runtime error when the app is not running or when called from the app thread (see Error handling). Exceptions raised by the callable are re-raised on the calling thread under the rules in Workflows step 5.

## Module architecture

- The method belongs on the App class in the app module, grouped with the other App-level methods. It must not be placed in the message pump, widgets, or drivers.
- The thread-entry values belong to the App and are initialized in the App constructor.
- Setting and clearing the thread-entry values belongs inside the run entry point, the coroutine that awaits the App's async main. It must not be placed in the synchronous run method that creates and drives the event loop, because that method's cleanup runs only after loop teardown. It must not be placed in message processing.
- Reuse existing mechanisms: the App's existing active-app helper, the invoke helper from the callback module, and the standard threadsafe scheduling of a coroutine onto a given event loop.

## Implementation constraints

- Do not reimplement awaitable handling or argument invocation. Calls to the callable must go through the existing invoke helper.
- Do not add a parallel callback-invocation path.
- The active-app setting must occur inside the scheduled work before the callable is invoked. Setting it on the calling thread has no effect on the scheduled work.
- The not-running check must rely on the cleared state after shutdown, not on a separate flag.
- Positional arguments must be bound to the callable before the invoke helper is used; they must not be passed to the invoke helper as its own parameters (see Workflows 3b).
- Do not capture the callable's outcome (value or exception) inside the scheduled work, do not wrap the callable in a result-carrying tuple or a separate future, and do not catch exceptions around the scheduled work. The outcome is read only from the scheduled result (see Workflows 4 and 5). Custom outcome capture is the wrong way to preserve exceptions: it is not required by the contract and diverges from the reference.
- Do not add a polling loop, timed retries, or periodic state re-checks around the wait (see Reliability).

## Dependencies

- No new third-party dependencies.
- Use only standard-library modules that the app module already has or can import from the standard library (threading, asyncio, the future type from concurrent.futures, and partial binding from functools), plus the existing invoke helper and active-app variable.

## Error handling

- Not running: raise a runtime error with the exact message "App is not running".
- Same thread: raise a runtime error with the exact message "The `call_from_thread` method must run in a different thread from the app". The message must not describe the not-running case.
- Exceptions raised by the callable are not swallowed, wrapped, retried, or treated specially because of their type. This includes exceptions that are timeout exceptions on some Python versions. The re-creation of exact concurrent.futures types by asyncio's bridge (Workflows 5) is expected behaviour, not an error to handle.
- Shutdown: calls made after shutdown are rejected by the not-running check at entry and therefore never block. The method must not add a mechanism that watches loop state during the wait to detect shutdown.

## Naming

- Test functions in the new test module must have names that describe exactly what each test verifies. Test comments must match the code they describe (for example, the exit value a test uses). Misspelled or stale names and comments are not acceptable.

## Documentation

- The method must have a docstring that states that Textual objects are not thread-safe, that the call ensures the code runs in the correct context, and that the call blocks until the callable returns.
- The docstring's Args section must describe the callable and the forwarded arguments.
- The docstring's Raises section must document both runtime error cases: the app not running (including after it has stopped) and the call from the app thread.

## Reliability

- The method blocks the calling thread only until the scheduled callable completes. It does this with a single blocking wait on the scheduled result, not with timed waits in a loop.
- Thread-entry state must be cleared on every exit path of the run entry point, including exceptions, and before the event loop begins its own teardown. This ensures no call after shutdown can be scheduled onto a loop that will never run it and then wait on it.

## Maintainability

- New standard-library imports must be placed in the module's existing import block in the order used there (sorted by module name, as the existing imports are), not appended or inserted out of order.

## Compatibility

- The project declares Python 3.7 and later. The required outcomes must hold on every supported version: the returned value, the not-running and same-thread runtime errors, exception propagation to the calling thread, and no blocking after shutdown.
- The exact class a timeout-class exception has on the calling thread depends on the running interpreter's asyncio (Workflows 5). Do not normalize it in the implementation, and do not require one specific class in tests.
- Use only APIs available on the minimum supported version. For example, do not use asyncio.to_thread in the implementation or in tests.
- Any new module, including a test module, must import on the minimum supported version. Builtin generic annotations (for example tuple or list subscripted forms) that are evaluated at import time, such as in a module-level function signature, require the future-annotations import at the top of the module or the equivalent typing names. Follow the repository convention of starting modules with the future-annotations import when they use such annotations.

## Behavioral acceptance criteria

- A background thread calling the method with a callable that writes to a text log widget in the app causes the write to occur and the method to return.
- A callable that returns an awaitable is awaited, and its result is returned to the calling thread.
- A callable that raises a timeout-class exception (for example, one raised by a third-party timeout) causes an exception with the same message and arguments to be raised on the calling thread, and the call returns instead of hanging. The exception may be the asyncio-converted class described in Workflows 5.
- A callable that accepts variadic arguments receives all supplied positional arguments, and a callable with named parameters receives the supplied keyword arguments.
- A call from the app thread raises a runtime error.
- A call before the app runs raises the "App is not running" runtime error.
- A call made after the app's run has returned raises the "App is not running" runtime error and does not block.
- A background thread that calls the app's exit through the method causes run to return the supplied exit value.

## Test requirements

- Place the tests in a concurrency-focused test module under the tests directory, following the repository's test naming convention.
- Drive the app with a headless run from the test's main thread. Start the background calling thread from the app's ready hook (or after mount) so that the cross-thread calls happen once the app is running.
- Background threads started by tests must not keep the test process alive. Make them daemon threads. After the run returns, join each such thread with a bounded wait and assert that it has finished; a thread still alive is a test failure.
- Do not issue a test's final cross-thread call from a cleanup path that can run after the app has stopped. Every cross-thread call a test makes must be issued while the app is running, and its outcome must be checked.
- The test run must terminate by itself. A test process that hangs after its tests report success counts as a failing check.
- Test code must not create, start, or drive its own event loop, and must not use APIs unavailable on the minimum supported Python version (see Compatibility).
- Tests must not read private App attributes (such as loop or thread-identifier state). Verify behaviour through public results: the callable's return value, the value the app's run returns, and raised exceptions.
- For exception propagation, assert that an exception is raised on the calling thread with the expected message and arguments, and that the call returns. Do not assert object identity or the exact concurrent.futures class of a timeout-class exception, and do not write tests whose pass or fail status depends on whether the builtin timeout error and the concurrent.futures timeout error are the same type.
- The widget-access test must not assert rendered or layout-dependent widget state (for example, line counts after a write), because widgets may not be laid out when the call happens. Verify that the callable completes without error and that the app exits with a supplied code.
- Every test in the new module must pass on the recorded Python environment before the work is considered done.
- Cover: the not-running case, the same-thread case, widget access from within the callable, an awaitable callable, exception propagation (including a timeout-class exception), argument forwarding to a variadic callable, and a call after the app has stopped.

