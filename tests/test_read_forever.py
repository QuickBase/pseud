import asyncio
import pytest
from pseud.common import read_forever


class FakeSocket:
    """Feeds queued messages to read_forever like an async zmq socket."""

    def __init__(self):
        self.queue = asyncio.Queue()

    async def recv_multipart(self, copy=False):
        return await self.queue.get()


async def wait_for_condition(condition, timeout=2):
    async def poll():
        while not condition():
            await asyncio.sleep(0.01)

    await asyncio.wait_for(poll(), timeout)


@pytest.mark.asyncio
async def test_read_forever_survives_callback_exception():
    """An exception escaping the message callback must not kill the reader.

    The reader is the only consumer of the shared socket - if it dies, every
    peer is cut off until a manual restart. A bad message should be dropped
    and the next one processed normally.
    """
    socket = FakeSocket()
    processed = []

    async def callback(message):
        if message == [b'boom']:
            raise ValueError('boom')
        processed.append(message)

    reader = asyncio.get_event_loop().create_task(read_forever(socket, callback))
    try:
        socket.queue.put_nowait([b'boom'])
        socket.queue.put_nowait([b'fine'])

        await wait_for_condition(lambda: processed or reader.done())

        assert processed == [[b'fine']]
        assert not reader.done()
    finally:
        reader.cancel()
        with pytest.raises(asyncio.CancelledError):
            await reader


@pytest.mark.asyncio
async def test_read_forever_cancellation_propagates():
    """Cancelling the reader while it is inside the callback must still work."""
    socket = FakeSocket()
    entered_callback = asyncio.Event()

    async def callback(message):
        entered_callback.set()
        await asyncio.sleep(60)

    reader = asyncio.get_event_loop().create_task(read_forever(socket, callback))
    socket.queue.put_nowait([b'slow'])

    await asyncio.wait_for(entered_callback.wait(), 2)
    reader.cancel()
    with pytest.raises(asyncio.CancelledError):
        await reader
    assert reader.cancelled()
