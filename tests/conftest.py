import asyncio
import os
import stat

import pytest
import pytest_asyncio
import zmq.asyncio


@pytest_asyncio.fixture
async def loop():
    # pytest-asyncio drives each async test on its own loop and no longer
    # lets a same-named fixture override it, so grab that loop instead of
    # creating a separate one that the test wouldn't actually run on.
    return asyncio.get_running_loop()


@pytest.fixture(autouse=True)
def close_context():
    yield
    context = zmq.asyncio.Context.instance()
    context.destroy(linger=0)
