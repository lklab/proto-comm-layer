import asyncio
from enum import Enum
from collections import deque
from typing import Callable, Deque, Any
import uuid
import time

from stream_handler import StreamHandler
from message_parser import MessageParser
from configs import MessageHandlerConfig

class MessageState(Enum) :
    CONNECTED = 1
    DISCONNECTED = 2

class MessageHandler :
    def __init__(
            self,
            stream: StreamHandler,
            on_message: Callable[[Any], None],
            on_disconnected: Callable[[], None],
            parser: MessageParser,
            config: MessageHandlerConfig,
        ) :
        self.state = MessageState.CONNECTED

        self.stream = stream
        self.host = stream.host
        self.port = stream.port

        self.on_message = on_message
        self.on_disconnected = on_disconnected

        self.parser = parser
        self.config = config

        self.send_task: asyncio.Task = None
        self.send_queue: Deque[tuple[int, bytes]] = deque()
        self.response_futures: dict[str, asyncio.Future] = {}

        self._security_no_comm_check_task: asyncio.Task = None
        self._security_last_comm_time: float = time.monotonic()
        self._security_comm_count: int = 0
        self._security_reset_comm_limit_task: asyncio.Task = None

        if not self.stream.is_trust() :
            self._security_start_no_comm_check_task()
            self._security_start_reset_comm_limit_task()

        self.stream.add_disconnected_event(self._on_disconnected)
        self.stream.listen(self._on_data)

    def send(self, message) :
        if self.state != MessageState.CONNECTED :
            return
        self._send(message)

    async def asend(self, message, timeout: float = 10) :
        if self.state != MessageState.CONNECTED :
            return

        rqid = str(uuid.uuid4())
        message.rqid = rqid

        future = asyncio.Future()
        self.response_futures[rqid] = future

        self._send(message)

        try:
            return await asyncio.wait_for(future, timeout)
        except :
            raise
        finally :
            del self.response_futures[rqid]

    def disconnect(self) :
        if self.state == MessageState.DISCONNECTED :
            return
        self.state = MessageState.DISCONNECTED

        self._security_stop_no_comm_check_task()
        self._security_stop_reset_comm_limit_task()

        asyncio.create_task(self._disconnect_task())

    def _send(self, message) :
        message_code = self.parser.type_to_code(type(message))
        if message_code != None :
            data = message.SerializeToString()
            self.send_queue.append((message_code, data))

            if self.send_task == None :
                self.send_task = asyncio.create_task(self._send_queued_messages())

    def _on_data(self, message_code: int, data: bytes) :
        if self.state == MessageState.DISCONNECTED :
            return

        if not self.stream.is_trust() :
            self._security_last_comm_time = time.monotonic()

            if self._security_comm_count >= self.config.comm_count_limit :
                self.disconnect()
                return
            self._security_comm_count += 1

        message = self.parser.parse(message_code, data)
        if message == None :
            self.stream.add_fail_count()
            return
        self.stream.reset_fail_count()

        if hasattr(message, 'rqid') and message.rqid in self.response_futures :
            future = self.response_futures.pop(message.rqid, None)
            if future != None and not future.done() :
                future.set_result(message)
        else :
            self.on_message(message)

    def _on_disconnected(self) :
        self.state = MessageState.DISCONNECTED
        self.on_disconnected()

    async def _send_queued_messages(self) :
        while len(self.send_queue) > 0 :
            message_code, data = self.send_queue[0]
            success = await self.stream.send(message_code, data)
            if success :
                self.send_queue.popleft()
            else :
                break

        self.send_task = None

    async def _disconnect_task(self) :
        if self.send_task != None :
            send_task: asyncio.Task = self.send_task
            await send_task

        await self.stream.close()

    def _security_start_no_comm_check_task(self) :
        async def _task() :
            while True :
                await asyncio.sleep(self.config.no_comm_limit_check_period_seconds)
                diff: float = time.monotonic() - self._security_last_comm_time
                if diff > self.config.no_comm_limit :
                    self.disconnect()
                    return

        self._security_no_comm_check_task = asyncio.create_task(_task())

    def _security_stop_no_comm_check_task(self) :
        async def _task() :
            if self._security_no_comm_check_task != None :
                task = self._security_no_comm_check_task
                self._security_no_comm_check_task = None

                task.cancel()
                try :
                    await task
                except :
                    pass

        asyncio.create_task(_task())

    def _security_start_reset_comm_limit_task(self) :
        async def _task() :
            while True :
                await asyncio.sleep(self.config.comm_count_limit_reset_period_seconds)
                self._security_comm_count = 0

        self._security_reset_comm_limit_task = asyncio.create_task(_task())

    def _security_stop_reset_comm_limit_task(self) :
        async def _task() :
            if self._security_reset_comm_limit_task != None :
                task = self._security_reset_comm_limit_task
                self._security_reset_comm_limit_task = None

                task.cancel()
                try :
                    await task
                except :
                    pass

        asyncio.create_task(_task())
