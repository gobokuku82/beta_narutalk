"""
Triple Server Startup Script
Chat API (Port 8001), Database API (Port 8002), Frontend (Port 8080)을 동시에 실행
"""

import subprocess
import sys
import os
import time
import signal
import asyncio
import httpx
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServerManager:
    """서버 프로세스 관리자"""

    def __init__(self):
        self.processes = {}
        self.running = True

    def start_frontend_server(self, port: int = 8080) -> subprocess.Popen:
        """
        Frontend 서버 시작

        Args:
            port: 포트 번호 (기본값: 8080)

        Returns:
            서버 프로세스
        """
        logger.info(f"Starting Frontend Server on port {port}...")

        # frontend 디렉토리로 이동하여 http.server 실행
        frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")

        cmd = [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--directory", frontend_dir
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        self.processes["Frontend Server"] = process
        logger.info(f"Frontend Server started with PID: {process.pid}")

        return process

    def start_server(self, name: str, module: str, port: int) -> subprocess.Popen:
        """
        서버 시작

        Args:
            name: 서버 이름
            module: 실행할 모듈 경로
            port: 포트 번호

        Returns:
            서버 프로세스
        """
        logger.info(f"Starting {name} on port {port}...")

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            module,
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        self.processes[name] = process
        logger.info(f"{name} started with PID: {process.pid}")

        return process

    async def check_health(self, url: str, max_retries: int = 30) -> bool:
        """
        서버 헬스 체크

        Args:
            url: 헬스체크 URL
            max_retries: 최대 재시도 횟수

        Returns:
            서버 상태 (True/False)
        """
        async with httpx.AsyncClient() as client:
            for i in range(max_retries):
                try:
                    response = await client.get(url, timeout=2.0)
                    if response.status_code == 200:
                        return True
                except:
                    pass

                if i < max_retries - 1:
                    await asyncio.sleep(1)

        return False

    async def wait_for_servers(self):
        """모든 서버가 준비될 때까지 대기"""
        logger.info("Waiting for servers to be ready...")

        # Database API 체크
        db_ready = await self.check_health("http://localhost:8002/")
        if db_ready:
            logger.info("✅ Database API is ready")
        else:
            logger.error("❌ Database API failed to start")

        # Chat API 체크
        chat_ready = await self.check_health("http://localhost:8001/")
        if chat_ready:
            logger.info("✅ Chat API is ready")
        else:
            logger.error("❌ Chat API failed to start")

        # Frontend 서버 체크 (간단한 체크 - http.server는 보통 즉시 시작됨)
        frontend_ready = await self.check_health("http://localhost:8080/test_chat.html")
        if frontend_ready:
            logger.info("✅ Frontend Server is ready")
        else:
            logger.error("❌ Frontend Server failed to start")

        if db_ready and chat_ready and frontend_ready:
            logger.info("=" * 60)
            logger.info("🚀 All servers are running!")
            logger.info("=" * 60)
            logger.info("📍 Database API: http://localhost:8002")
            logger.info("   - Docs: http://localhost:8002/docs")
            logger.info("📍 Chat API: http://localhost:8001")
            logger.info("   - Docs: http://localhost:8001/docs")
            logger.info("🌐 Frontend: http://localhost:8080/test_chat.html")
            logger.info("=" * 60)
            logger.info("Press Ctrl+C to stop all servers")
            return True
        else:
            logger.error("Failed to start all servers")
            return False

    def monitor_processes(self):
        """프로세스 모니터링"""
        while self.running:
            for name, process in self.processes.items():
                if process.poll() is not None:
                    logger.warning(f"{name} has stopped (exit code: {process.returncode})")
                    # 재시작 로직을 여기에 추가할 수 있음

            time.sleep(5)

    def stop_all(self):
        """모든 서버 중지"""
        logger.info("Stopping all servers...")
        self.running = False

        for name, process in self.processes.items():
            if process.poll() is None:
                logger.info(f"Stopping {name} (PID: {process.pid})")
                process.terminate()

                # 정상 종료 대기
                try:
                    process.wait(timeout=5)
                    logger.info(f"{name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    # 강제 종료
                    logger.warning(f"Force killing {name}")
                    process.kill()
                    process.wait()

        logger.info("All servers stopped")


async def main():
    """메인 실행 함수"""
    manager = ServerManager()

    # 시그널 핸들러 등록
    def signal_handler(signum, frame):
        logger.info(f"\nReceived signal {signum}")
        manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 1. Database API 시작 (Port 8002)
        manager.start_server(
            "Database API",
            "database.api.main:app",
            8002
        )

        # Database API가 시작될 때까지 잠시 대기
        await asyncio.sleep(3)

        # 2. Chat API 시작 (Port 8001)
        manager.start_server(
            "Chat API",
            "backend.api.main:app",
            8001
        )

        # Chat API가 시작될 때까지 잠시 대기
        await asyncio.sleep(2)

        # 3. Frontend 서버 시작 (Port 8080)
        manager.start_frontend_server(8080)

        # 4. 서버들이 준비될 때까지 대기
        success = await manager.wait_for_servers()

        if success:
            # 4. 프로세스 모니터링 (블로킹)
            manager.monitor_processes()
        else:
            manager.stop_all()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received")
        manager.stop_all()
    except Exception as e:
        logger.error(f"Error: {e}")
        manager.stop_all()
        sys.exit(1)


if __name__ == "__main__":
    # Windows에서 Ctrl+C 처리 개선
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 실행
    asyncio.run(main())