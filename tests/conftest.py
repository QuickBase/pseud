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


@pytest.fixture(autouse=True)
def cleanup_ipc_sockets():
    # ipc:// endpoints bind a real unix socket file on disk, and closing
    # the socket doesn't unlink it. Several tests bind relative, bare
    # names (e.g. 'ipc://here'), which land in the cwd pytest runs from.
    # Remove whatever socket files show up there during the test.
    cwd = os.getcwd()
    before = set(os.listdir(cwd))
    yield
    after = set(os.listdir(cwd))
    for name in after - before:
        path = os.path.join(cwd, name)
        try:
            if stat.S_ISSOCK(os.stat(path).st_mode):
                os.unlink(path)
        except OSError:
            pass
