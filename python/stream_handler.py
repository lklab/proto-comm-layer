import asyncio
from typing import Callable
from enum import Enum
import traceback

from configs import StreamHandlerConfig

class StreamState(Enum) :
    INITIALIZED = 0
    LISTENING = 1
    DISCONNECTED = 2

class StreamHandler :
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, config: StreamHandlerConfig) :
        self.state = StreamState.INITIALIZED

        self.reader = reader
        self.writer = writer
        self.config = config

        self.host: str = self.writer.get_extra_info('peername')[0]
        self.port: int = self.writer.get_extra_info('peername')[1]

        self.listen_task: asyncio.Task = None
        self.disconnected_event: list[Callable[[], StreamHandler]] = []

        self.failCount: int = 0

    def add_disconnected_event(self, listener: Callable[[], None]) :
        self.disconnected_event.append(listener)

    def remove_disconnected_event(self, listener: Callable[[], None]) :
        self.disconnected_event.remove(listener)

    def listen(self, on_data: Callable[[int, bytes], None]) :
        if self.state != StreamState.INITIALIZED :
            return
        self.state = StreamState.LISTENING

        self.listen_task = asyncio.create_task(self._listen(on_data))

    def is_trust(self) -> bool :
        return self.config.trust

    async def _listen(self, on_data: Callable[[int, bytes], None]) :
        buffer = b''

        try:
            while True:
                chunk = await self.reader.read(self.config.read_size)
                if not chunk or self.state == StreamState.DISCONNECTED :
                    break
                buffer += chunk

                while True :
                    # check delimiter
                    cursor = buffer.find(self.config.delimiter)
                    if cursor == -1 :
                        buffer = b''
                        self.add_fail_count()
                        break
                    cursor += 4

                    # get message type and payload size
                    if len(buffer) < cursor + 8 :
                        break
                    message_code = int.from_bytes(buffer[cursor:cursor+4], byteorder='big')
                    cursor += 4
                    payload_size = int.from_bytes(buffer[cursor:cursor+4], byteorder='big')
                    cursor += 4

                    # check payload size
                    if payload_size > self.config.max_payload_size :
                        buffer = buffer[cursor:]
                        self.add_fail_count()
                        continue

                    # get payload
                    if len(buffer) < cursor + payload_size :
                        break
                    payload = buffer[cursor:cursor+payload_size]
                    cursor += payload_size

                    # remove one message
                    buffer = buffer[cursor:]

                    try :
                        # forward payload
                        on_data(message_code, payload)
                    except Exception :
                        traceback.print_exc()

        except asyncio.CancelledError:
            pass

        except Exception :
            traceback.print_exc()

        self.listenTask = None
        await self.close()

    async def send(self, type: int, payload: bytes) -> bool :
        if self.state != StreamState.LISTENING :
            return False

        data = (
            self.config.delimiter +
            type.to_bytes(4, byteorder='big') +
            len(payload).to_bytes(4, byteorder='big') +
            payload
        )

        try:
            self.writer.write(data)
            await self.writer.drain()

        except (OSError, asyncio.CancelledError, BrokenPipeError, ConnectionResetError) :
            await self.close()
            return False

        return True

    def add_fail_count(self) :
        if self.config.trust :
            return

        self.failCount += 1
        if self.failCount >= self.config.max_fail_count :
            asyncio.create_task(self.close())

    def reset_fail_count(self) :
        self.failCount = 0

    async def close(self) :
        if self.state == StreamState.DISCONNECTED :
            return
        self.state = StreamState.DISCONNECTED

        # cancel listen task
        if self.listen_task != None :
            task = self.listen_task
            self.listen_task = None

            try :
                task.cancel()
                await task
            except :
                pass

        # close writer
        try :
            self.writer.close()
            await self.writer.wait_closed()
        except :
            pass

        try :
            for listener in self.disconnected_event :
                listener()
        except :
            pass
