# Call from thread method

## Goals

- Provide a public method on the application object that lets code running on a non-app thread (for example, a worker thread wrapping a third-party threaded API) run a callable in the app's context and receive its result. Integrators should not have to manage the app's event loop themselves.
- Keep behaviour predictable: the call blocks the calling thread until the callable has finished, then returns its result.
- This is a step toward an integration answer for third-party APIs. Syntactic sugar and further convenience APIs are deferred.

## Scope

- In scope: one new public method on the App class; the thread-entry state the method needs; lifecycle bookkeeping in the app's run entry point; and tests for the behaviours listed below.
- Out of scope: changes to widgets, the message pump, or drivers; new convenience wrappers; async-native alternatives.

## Assumptions

- The app's run entry point is the only place the app's event loop starts and stops. Thread-entry state must therefore be owned there.

## Terminology

- App thread: the thread that calls the app's run entry point and on which the app's event loop runs.
- Calling thread: any thread other than the app thread.
- App context: the framework's active-app context variable. Framework code such as widget access through the app property resolves the app from it, and it is per asyncio task, so it must be established inside the task that runs the callable.

## Workflows

The method must check the following conditions in this order:

1. If the app is not running (no event loop has been recorded), raise a runtime error with the message "App is not running". This applies before the app has started and after it has stopped.
2. If the calling thread is the app thread, raise a runtime error whose message states that the call must run in a different thread from the app.
3. Otherwise, schedule work onto the app's event loop in a thread-safe way. The scheduled task must:
   a. Set the app as the active app in the app context for that task.
   b. Invoke the callable with the supplied positional and keyword arguments through the existing invoke helper, which awaits the result when the callable returns an awaitable.
4. The calling thread blocks until the scheduled work completes, then returns the callable's result.
5. If the callable raises, the exception propagates to the calling thread.
6. Callables that touch widgets through the app (for example, querying a widget and writing to it) must succeed when called this way.

Lifecycle: the app's run entry point records the event loop and the app thread's identifier when the app starts running. When the run entry point finishes, for any reason including an error, it clears both records so that later calls follow step 1 and raise instead of waiting.

## Data model

- The App holds two thread-entry values: a reference to the app's event loop, and the identifier of the app thread.
- Both are empty when the App is constructed, so a call made before run is detected as not running.
- Both are set at the start of the run entry point, from the thread that invokes run.
- Both are cleared in a cleanup step that always executes when the run entry point ends, so a finished app is never reported as running.

## API contracts

- A public method named call_from_thread on the App class.
- Input: a required callable that may return a value or an awaitable of a value; followed by any positional arguments and any keyword arguments, all forwarded to the callable.
- Return: the callable's result, after awaiting if needed. Annotate the return type with a generic type variable tied to the callable's result type, and annotate the callable parameter as a callable returning either that type or an awaitable of it. Do not use an untyped return.
- Raises a runtime error when the app is not running or when called from the app thread (see Error handling). Exceptions raised by the callable propagate unchanged.

## Module architecture

- The method belongs on the App class in the app module, grouped with the other App-level methods. It must not be placed in the message pump, widgets, or drivers.
- The thread-entry values belong to the App and are initialized in the App constructor.
- Setting and clearing the thread-entry values belongs to the run entry point of the App, not to message processing.
- Reuse existing mechanisms: the App's existing active-app setter, the invoke helper from the callback module, and the standard threadsafe scheduling of a coroutine onto a given event loop.

## Implementation constraints

- Do not reimplement awaitable handling or argument invocation. Calls to the callable must go through the existing invoke helper.
- Do not add a parallel callback-invocation path.
- The active-app setting must occur inside the scheduled task before the callable is invoked. Setting it on the calling thread has no effect on the scheduled task.
- The not-running check must rely on the cleared state after shutdown, not on a separate flag.

## Dependencies

- No new third-party dependencies.
- Use only standard-library modules that the app module already has or can import from the standard library (threading, asyncio, the future type from concurrent.futures, and partial binding from functools), plus the existing invoke helper and active-app variable.

## Error handling

- Not running: raise a runtime error with the exact message "App is not running".
- Same thread: raise a runtime error whose message says the call_from_thread method must run in a different thread from the app. The message must not describe the not-running case.
- Exceptions raised by the callable are not swallowed or wrapped.
- Calls after shutdown must raise, never block. A call must never wait indefinitely on work the app can no longer run.

## Documentation

- The method must have a docstring that states that Textual objects are not thread-safe, that the call ensures the code runs in the correct context, and that the call blocks until the callable returns.
- The docstring's Args section must describe the callable and the forwarded arguments.
- The docstring's Raises section must document both runtime error cases: the app not running (including after it has stopped) and the call from the app thread.

## Reliability

- The method blocks the calling thread only until the scheduled callable completes.
- Thread-entry state must be cleared on every exit path of the run entry point, including exceptions, so no call after shutdown can wait on a stopped loop.

## Behavioral acceptance criteria

- A background thread calling the method with a callable that writes to a text log widget in the app causes the write to occur and the method to return.
- A callable that returns an awaitable is awaited, and its result is returned to the calling thread.
- A call from the app thread raises a runtime error.
- A call before the app runs raises the "App is not running" runtime error.
- A call made after the app's run has returned raises the "App is not running" runtime error and does not block.
- A background thread that calls the app's exit through the method causes run to return the supplied exit value.

## Test requirements

- Place the tests in a concurrency-focused test module under the tests directory, following the repository's test naming convention.
- Drive the app with a headless run, and perform the cross-thread calls from a background thread that the test starts.
- Do not call the asyncio run function from inside synchronous tests. Doing so pollutes global event-loop state for later tests.
- Cover: the not-running case, the same-thread case, widget access from within the callable, an awaitable callable, exception propagation, and a call after the app has stopped.
