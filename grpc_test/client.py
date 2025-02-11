import sys
import asyncio

from grpc import aio
import echo_pb2
import echo_pb2_grpc


async def receive_state(stub):
    async for state in stub.StreamState(echo_pb2.Empty()):
        print(f"[STATE] request_count={state.request_count}")


async def main():
    # gRPC 채널/Stub 생성
    channel = aio.insecure_channel("localhost:50051")
    stub = echo_pb2_grpc.EchoServiceStub(channel)

    # 서버 스트리밍은 백그라운드 태스크로 돌림
    asyncio.create_task(receive_state(stub))

    print("Type your message (Ctrl+C to exit):")

    while True:
        # 동기적 stdin.readline()을 스레드에서 돌려, 코루틴으로 await
        line = await asyncio.to_thread(sys.stdin.readline)
        if not line:
            # EOF
            break

        line = line.strip()
        if not line:
            continue

        response = await stub.SendRequest(echo_pb2.Request(message=line))
        print("[RESPONSE]", response.message)


if __name__ == '__main__':
    asyncio.run(main())
