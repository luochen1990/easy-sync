Easy Async
==========

This is a WIP project without a proper implementation yet.

But tests are added, and things are strictly type checked here.

I would be extremely grateful if someone could contribute a proper implementation.

Any discussion about it's implementation is welcome [here](https://github.com/luochen1990/easy-async/discussions).

There is also a discussion on [StackOverflow Question](https://stackoverflow.com/questions/77274838/how-do-i-wrap-asyncio-calls-in-general-purpose-non-async-functions).

Run tests
---------

You can use `nix develop .` or `poetry shell` under the project root to enter the develop environment.

Currently, if you run `pytest` you will got:

```text
========================================== short test summary info ===========================================
FAILED test/bad_impl_1/test_impl_1.py::test_impl_1 - RuntimeError: asyncio.run() cannot be called from a running event loop
FAILED test/bad_impl_2/test_impl_2.py::test_impl_2 - RuntimeError: This function can only be run from an AnyIOworker thread
============================================= 2 failed in 3.06s ==============================================
```

