Call from thread method

This is a step towards having an answer to devs who want to integrate a third-party API with Textual.

The `call_from_thread` takes a callback that will be called in the app's loop from a thread. It will block until the callback returns. If integrating with a threaded API (many are under the hood), this will generally give the most predictable behaviour.

There are downsides: you call it from the same thread as the app. Otherwise it would deadlock.

I'll leave this method undocumented for now. We will at least have an answer for the next version, and we can work on greater syntactical sugar in the meantime.
