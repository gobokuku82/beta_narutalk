"""
대화형 테스트 클라이언트
터미널에서 직접 대화하며 Chat API를 테스트
"""

import asyncio
import httpx
import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
import time

# 색상 코드
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class InteractiveTester:
    """대화형 테스트 클라이언트"""

    def __init__(self, chat_url: str = "http://localhost:8001", db_url: str = "http://localhost:8002"):
        self.chat_url = chat_url
        self.db_url = db_url
        self.session_id = f"test_session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.user_id = "test_user"
        self.client = None
        self.conversation_history = []

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def check_servers(self) -> bool:
        """서버 상태 확인"""
        try:
            # Chat API 체크
            response = await self.client.get(f"{self.chat_url}/")
            if response.status_code != 200:
                print(f"{Colors.RED}❌ Chat API is not responding{Colors.ENDC}")
                return False

            # Database API 체크
            response = await self.client.get(f"{self.db_url}/")
            if response.status_code != 200:
                print(f"{Colors.RED}❌ Database API is not responding{Colors.ENDC}")
                return False

            print(f"{Colors.GREEN}✅ All servers are running{Colors.ENDC}")
            return True

        except Exception as e:
            print(f"{Colors.RED}❌ Server check failed: {e}{Colors.ENDC}")
            return False

    async def send_chat(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict:
        """Chat API로 메시지 전송"""
        request_data = {
            "query": query,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "context": context or {},
            "use_cache": True
        }

        start_time = time.time()

        try:
            response = await self.client.post(
                f"{self.chat_url}/api/v1/chat",
                json=request_data
            )

            elapsed_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                result['elapsed_time'] = elapsed_time

                # 대화 기록 저장
                self.conversation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "response": result['response'],
                    "elapsed_time": elapsed_time
                })

                return result
            else:
                return {
                    "error": f"API returned status {response.status_code}",
                    "detail": response.text,
                    "elapsed_time": elapsed_time
                }

        except Exception as e:
            return {
                "error": str(e),
                "elapsed_time": time.time() - start_time
            }

    def print_response(self, result: Dict):
        """응답 출력"""
        print("\n" + "="*80)

        if "error" in result:
            print(f"{Colors.RED}❌ Error: {result['error']}{Colors.ENDC}")
            if "detail" in result:
                print(f"Detail: {result['detail']}")
        else:
            # 응답 내용
            print(f"{Colors.GREEN}📝 Response:{Colors.ENDC}")
            print(result.get('response', 'No response'))

            # 메타데이터
            print(f"\n{Colors.BLUE}📊 Metadata:{Colors.ENDC}")
            print(f"  • Session ID: {result.get('session_id')}")
            print(f"  • Cached: {result.get('cached', False)}")
            print(f"  • Response Time: {result.get('response_time', 0):.2f}s")
            print(f"  • Total Time: {result.get('elapsed_time', 0):.2f}s")

            # 사용된 에이전트
            if 'agents_used' in result:
                print(f"\n{Colors.YELLOW}🤖 Agents Used:{Colors.ENDC}")
                for agent in result['agents_used']:
                    print(f"  • {agent}")

        print("="*80)

    def save_conversation(self):
        """대화 기록 저장"""
        filename = f"tests/test_results/responses/interactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "session_id": self.session_id,
                "user_id": self.user_id,
                "conversation": self.conversation_history
            }, f, ensure_ascii=False, indent=2)

        print(f"\n{Colors.GREEN}💾 Conversation saved to: {filename}{Colors.ENDC}")

    async def run_interactive_mode(self):
        """대화형 모드 실행"""
        print(f"\n{Colors.BOLD}🚀 Interactive Chat Test Client{Colors.ENDC}")
        print("="*80)
        print(f"Session ID: {self.session_id}")
        print(f"User ID: {self.user_id}")
        print(f"Chat API: {self.chat_url}")
        print(f"Database API: {self.db_url}")
        print("="*80)

        # 서버 상태 확인
        if not await self.check_servers():
            print(f"{Colors.RED}Please start the servers first:{Colors.ENDC}")
            print("  python run_servers.py")
            return

        print(f"\n{Colors.YELLOW}Commands:{Colors.ENDC}")
        print("  /help     - 도움말 표시")
        print("  /context  - 컨텍스트 설정")
        print("  /history  - 대화 기록 보기")
        print("  /save     - 대화 저장")
        print("  /clear    - 화면 지우기")
        print("  /exit     - 종료")
        print("\n예제 질문:")
        print("  • 2024년 11월 영업실적을 분석해줘")
        print("  • 김철수 직원의 정보를 알려줘")
        print("  • 리베이트 관련 규정을 설명해줘")
        print("="*80)

        context = {}

        while True:
            try:
                # 입력 받기
                query = input(f"\n{Colors.BOLD}You:{Colors.ENDC} ").strip()

                if not query:
                    continue

                # 명령어 처리
                if query.startswith("/"):
                    if query == "/exit":
                        print(f"{Colors.YELLOW}👋 Goodbye!{Colors.ENDC}")
                        break

                    elif query == "/help":
                        print(f"{Colors.BLUE}Available commands:{Colors.ENDC}")
                        print("  /help     - Show this help")
                        print("  /context  - Set context (role, department)")
                        print("  /history  - Show conversation history")
                        print("  /save     - Save conversation to file")
                        print("  /clear    - Clear screen")
                        print("  /exit     - Exit program")

                    elif query == "/context":
                        role = input("Role (e.g., 영업팀장): ").strip()
                        dept = input("Department (e.g., 영업1팀): ").strip()
                        context = {"role": role, "department": dept}
                        print(f"{Colors.GREEN}✅ Context updated: {context}{Colors.ENDC}")

                    elif query == "/history":
                        print(f"\n{Colors.BLUE}📜 Conversation History:{Colors.ENDC}")
                        for i, item in enumerate(self.conversation_history, 1):
                            print(f"\n{i}. [{item['timestamp']}]")
                            print(f"   Q: {item['query']}")
                            print(f"   A: {item['response'][:100]}...")

                    elif query == "/save":
                        self.save_conversation()

                    elif query == "/clear":
                        os.system('cls' if os.name == 'nt' else 'clear')

                    else:
                        print(f"{Colors.RED}Unknown command: {query}{Colors.ENDC}")

                    continue

                # Chat API 호출
                print(f"\n{Colors.YELLOW}⏳ Processing...{Colors.ENDC}")
                result = await self.send_chat(query, context)

                # 응답 출력
                print(f"\n{Colors.BOLD}AI:{Colors.ENDC}")
                self.print_response(result)

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}👋 Interrupted!{Colors.ENDC}")
                break

            except Exception as e:
                print(f"{Colors.RED}❌ Error: {e}{Colors.ENDC}")

        # 종료 시 저장 여부 확인
        if self.conversation_history:
            save = input("\nSave conversation? (y/n): ").strip().lower()
            if save == 'y':
                self.save_conversation()


async def main():
    """메인 함수"""
    try:
        async with InteractiveTester() as tester:
            await tester.run_interactive_mode()
    except Exception as e:
        print(f"{Colors.RED}Fatal error: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Goodbye!{Colors.ENDC}")