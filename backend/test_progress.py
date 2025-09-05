"""
진행 상황 업데이트 테스트 스크립트
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime


async def test_chat_with_progress():
    """채팅과 진행 상황 스트림 테스트"""
    
    base_url = "http://localhost:8000"
    session_id = str(uuid.uuid4())
    
    print(f"테스트 시작 - Session ID: {session_id}")
    print("=" * 50)
    
    # 1. SSE 연결을 위한 별도 태스크 시작
    async def monitor_sse():
        """SSE 스트림 모니터링"""
        print("\n[SSE] 진행 상황 스트림 연결 시작...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{base_url}/api/v1/chat/stream/{session_id}") as response:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data_str = line[6:]
                            try:
                                data = json.loads(data_str)
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                
                                if data['type'] == 'connection':
                                    print(f"[{timestamp}][SSE] ✅ 연결 성공")
                                elif data['type'] == 'progress':
                                    print(f"[{timestamp}][SSE] 📊 진행 상황: Step {data.get('current_step')}/{data.get('total_steps')} - {data.get('message')}")
                                    if data.get('active_agent'):
                                        print(f"[{timestamp}][SSE]    활성 에이전트: {data.get('active_agent')}")
                                elif data['type'] == 'completed':
                                    print(f"[{timestamp}][SSE] ✅ 처리 완료")
                                    break
                                elif data['type'] == 'error':
                                    print(f"[{timestamp}][SSE] ❌ 오류: {data.get('message')}")
                                    break
                                elif data['type'] == 'heartbeat':
                                    print(f"[{timestamp}][SSE] 💓 하트비트")
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                print(f"[SSE] 오류: {e}")
    
    # 2. 채팅 요청을 위한 태스크
    async def send_chat():
        """채팅 메시지 전송"""
        await asyncio.sleep(1)  # SSE 연결 대기
        
        print("\n[CHAT] 메시지 전송 중...")
        
        async with aiohttp.ClientSession() as session:
            # 복합 질의 전송
            request_data = {
                "query": "아스피린의 효능과 부작용을 알려주고, 관련 학술자료도 찾아줘",
                "session_id": session_id,
                "agents": ["info_retrieval"]  # 특정 에이전트 지정
            }
            
            try:
                async with session.post(
                    f"{base_url}/api/v1/chat/complex",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    
                    print("\n[CHAT] 응답 수신:")
                    print(f"  - Session ID: {result.get('session_id')}")
                    print(f"  - Agent Used: {result.get('agent_used')}")
                    
                    if result.get('metadata'):
                        agents_used = result['metadata'].get('agents_used', [])
                        if agents_used:
                            print(f"  - Agents Used: {', '.join(agents_used)}")
                        
                    print(f"\n[CHAT] 최종 응답:\n{result.get('response')[:200]}...")
                    
            except Exception as e:
                print(f"[CHAT] 오류: {e}")
    
    # 3. 진행 상황 조회 API 테스트
    async def check_progress():
        """진행 상황 API 직접 조회"""
        await asyncio.sleep(2)  # 처리 시작 대기
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{base_url}/api/v1/chat/progress/{session_id}") as response:
                    if response.status == 200:
                        progress = await response.json()
                        print(f"\n[API] 진행 상황 조회:")
                        print(f"  - Status: {progress.get('status')}")
                        print(f"  - Current Step: {progress.get('current_step')}")
                        print(f"  - Total Steps: {progress.get('total_steps')}")
                        print(f"  - Active Agent: {progress.get('active_agent')}")
            except Exception as e:
                print(f"[API] 진행 상황 조회 실패: {e}")
    
    # 태스크 동시 실행
    tasks = [
        asyncio.create_task(monitor_sse()),
        asyncio.create_task(send_chat()),
        asyncio.create_task(check_progress())
    ]
    
    # 모든 태스크 완료 대기
    await asyncio.gather(*tasks, return_exceptions=True)
    
    print("\n" + "=" * 50)
    print("테스트 완료")


async def test_debug_endpoints():
    """디버그 엔드포인트 테스트"""
    
    base_url = "http://localhost:8000"
    
    print("\n디버그 엔드포인트 테스트")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 모든 진행 상황 조회
        try:
            async with session.get(f"{base_url}/api/v1/chat/debug/all-progress") as response:
                if response.status == 200:
                    data = await response.json()
                    print("\n[DEBUG] 전체 진행 상황:")
                    print(f"  - 활성 연결: {len(data.get('active_connections', []))}")
                    print(f"  - 진행 중인 세션: {len(data.get('progress_sessions', []))}")
                    
                    if data.get('details'):
                        print("\n[DEBUG] 세션 상세:")
                        for sid, details in data['details'].items():
                            print(f"  - {sid[:8]}...")
                            print(f"    Status: {details.get('status')}")
                            print(f"    Step: {details.get('current_step')}/{details.get('total_steps')}")
        except Exception as e:
            print(f"[DEBUG] 오류: {e}")


async def main():
    """메인 테스트 실행"""
    
    print("\n🚀 Multi-Agent Supervisor 진행 상황 테스트")
    print("=" * 50)
    
    # 1. 채팅 및 진행 상황 테스트
    await test_chat_with_progress()
    
    # 2. 디버그 엔드포인트 테스트
    await test_debug_endpoints()
    
    print("\n✅ 모든 테스트 완료")


if __name__ == "__main__":
    asyncio.run(main())