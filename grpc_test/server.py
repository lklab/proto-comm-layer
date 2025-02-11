import asyncio
from grpc import aio  # asyncio 지원 API

import echo_pb2
import echo_pb2_grpc


class EchoService(echo_pb2_grpc.EchoServiceServicer):
    def __init__(self):
        # 이 예제에서는 락 없이 request_count 공유
        self.request_count = 0

    # (1) 단일 요청-응답: 클라이언트의 Request 개수 카운트 후, Echo 메시지 반환
    async def SendRequest(self, request, context):
        # 해당 함수 내에 명시적인 await가 없으므로
        # 중간에 컨텍스트 스위칭 없이 원자적으로 처리됨
        self.request_count += 1
        return echo_pb2.Response(message="Echo " + request.message)

    # (2) 서버 스트리밍: 5초마다 State (request_count) 전송
    async def StreamState(self, request, context):
        while True:
            # 클라이언트에게 현재 request_count 전송
            yield echo_pb2.State(request_count=self.request_count)
            # 이 부분에서 await가 발생하므로, 이벤트 루프는 다른 코루틴으로 전환 가능
            await asyncio.sleep(5)


async def serve():
    # asyncio 기반 gRPC 서버 생성
    server = aio.server()
    # 구현한 Servicer 등록
    echo_pb2_grpc.add_EchoServiceServicer_to_server(EchoService(), server)
    
    # 포트 바인딩
    server.add_insecure_port('[::]:50051')
    
    # 서버 시작
    await server.start()
    print("Async gRPC server started on port 50051.")
    
    # 종료 대기
    await server.wait_for_termination()


if __name__ == '__main__':
    asyncio.run(serve())
