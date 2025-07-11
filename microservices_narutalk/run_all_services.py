#!/usr/bin/env python3
"""
NaruTalk 마이크로서비스 통합 실행 스크립트
모든 서비스를 한번에 시작하고 관리합니다.
"""

import os
import sys
import time
import signal
import asyncio
import logging
import subprocess
from typing import List, Dict, Any
from pathlib import Path
import psutil

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 서비스 설정
SERVICES = [
    {
        "name": "Django Manager",
        "type": "django",
        "port": 8000,
        "path": "django_manager",
        "command": ["python", "manage.py", "runserver", "0.0.0.0:8000"],
        "health_check": "http://localhost:8000/health"
    },
    {
        "name": "Enhanced Router Agent",
        "type": "fastapi",
        "port": 8001,
        "path": "agents/router_agent",
        "command": ["python", "enhanced_main.py"],
        "health_check": "http://localhost:8001/health"
    },
    {
        "name": "Document Agent",
        "type": "fastapi",
        "port": 8002,
        "path": "agents/document_agent",
        "command": ["python", "main.py"],
        "health_check": "http://localhost:8002/health"
    },
    {
        "name": "Employee Agent",
        "type": "fastapi",
        "port": 8003,
        "path": "agents/employee_agent",
        "command": ["python", "main.py"],
        "health_check": "http://localhost:8003/health"
    },
    {
        "name": "Client Agent",
        "type": "fastapi",
        "port": 8004,
        "path": "agents/client_agent",
        "command": ["python", "main.py"],
        "health_check": "http://localhost:8004/health"
    },
    {
        "name": "General Agent",
        "type": "fastapi",
        "port": 8005,
        "path": "agents/general_agent",
        "command": ["python", "main.py"],
        "health_check": "http://localhost:8005/health"
    }
]

class ServiceManager:
    def __init__(self):
        self.services = SERVICES
        self.processes: Dict[str, subprocess.Popen] = {}
        self.project_root = Path(__file__).parent.absolute()
        
    def check_port_available(self, port: int) -> bool:
        """포트 사용 가능 여부 확인"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return False
            return True
        except:
            return True
    
    def kill_process_on_port(self, port: int):
        """포트에서 실행 중인 프로세스 종료"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.info['connections'] or []:
                        if conn.laddr.port == port:
                            logger.info(f"Killing process {proc.info['pid']} on port {port}")
                            proc.kill()
                            time.sleep(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logger.warning(f"Failed to kill process on port {port}: {e}")
    
    def start_service(self, service: Dict[str, Any]) -> bool:
        """서비스 시작"""
        try:
            # 포트 확인 및 정리
            if not self.check_port_available(service['port']):
                logger.warning(f"Port {service['port']} is already in use. Trying to free it...")
                self.kill_process_on_port(service['port'])
                time.sleep(2)
            
            # 서비스 디렉토리로 이동
            service_path = self.project_root / service['path']
            if not service_path.exists():
                logger.error(f"Service path not found: {service_path}")
                return False
            
            # 환경변수 설정
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.project_root)
            
            # Django 서비스 특별 처리
            if service['type'] == 'django':
                # Django 데이터베이스 마이그레이션
                try:
                    subprocess.run(
                        ["python", "manage.py", "migrate"],
                        cwd=service_path,
                        env=env,
                        capture_output=True,
                        text=True
                    )
                    logger.info(f"Django migrations completed for {service['name']}")
                except Exception as e:
                    logger.warning(f"Django migration failed: {e}")
            
            # 서비스 시작
            logger.info(f"Starting {service['name']} on port {service['port']}")
            
            process = subprocess.Popen(
                service['command'],
                cwd=service_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[service['name']] = process
            
            # 서비스 시작 대기
            time.sleep(3)
            
            # 프로세스 상태 확인
            if process.poll() is None:
                logger.info(f"✅ {service['name']} started successfully (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"❌ {service['name']} failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start {service['name']}: {e}")
            return False
    
    def stop_service(self, service_name: str):
        """서비스 중지"""
        if service_name in self.processes:
            process = self.processes[service_name]
            try:
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"✅ {service_name} stopped gracefully")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.info(f"⚠️ {service_name} force killed")
            except Exception as e:
                logger.error(f"❌ Failed to stop {service_name}: {e}")
            finally:
                del self.processes[service_name]
    
    def stop_all_services(self):
        """모든 서비스 중지"""
        logger.info("Stopping all services...")
        for service_name in list(self.processes.keys()):
            self.stop_service(service_name)
    
    def start_all_services(self):
        """모든 서비스 시작"""
        logger.info("🚀 Starting all NaruTalk microservices...")
        
        success_count = 0
        total_count = len(self.services)
        
        # 서비스 순차적 시작 (의존성 순서 고려)
        for service in self.services:
            if self.start_service(service):
                success_count += 1
            else:
                logger.error(f"Failed to start {service['name']}")
        
        # 결과 출력
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 Service startup completed: {success_count}/{total_count} services running")
        logger.info(f"{'='*60}")
        
        if success_count > 0:
            logger.info("🌐 Running services:")
            for service_name, process in self.processes.items():
                service_config = next(s for s in self.services if s['name'] == service_name)
                logger.info(f"  • {service_name} - http://localhost:{service_config['port']}")
        
        return success_count == total_count
    
    def monitor_services(self):
        """서비스 상태 모니터링"""
        logger.info("👁️ Monitoring services (Press Ctrl+C to stop all services)")
        
        try:
            while True:
                # 프로세스 상태 확인
                for service_name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        logger.error(f"❌ {service_name} has stopped unexpectedly")
                        del self.processes[service_name]
                
                # 상태 출력
                if len(self.processes) == 0:
                    logger.error("All services have stopped")
                    break
                
                time.sleep(10)  # 10초마다 체크
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown signal received")
            self.stop_all_services()
    
    def health_check_all(self):
        """모든 서비스 헬스 체크"""
        try:
            import requests
            
            logger.info("🔍 Performing health checks...")
            
            healthy_services = []
            unhealthy_services = []
            
            for service in self.services:
                try:
                    response = requests.get(service['health_check'], timeout=5)
                    if response.status_code == 200:
                        healthy_services.append(service['name'])
                        logger.info(f"✅ {service['name']} - Healthy")
                    else:
                        unhealthy_services.append(service['name'])
                        logger.warning(f"⚠️ {service['name']} - Unhealthy (Status: {response.status_code})")
                except Exception as e:
                    unhealthy_services.append(service['name'])
                    logger.error(f"❌ {service['name']} - Error: {e}")
            
            logger.info(f"\n📊 Health Check Summary:")
            logger.info(f"  Healthy: {len(healthy_services)}/{len(self.services)}")
            logger.info(f"  Unhealthy: {len(unhealthy_services)}/{len(self.services)}")
            
            return len(unhealthy_services) == 0
            
        except ImportError:
            logger.warning("requests library not available for health checks")
            return False


def main():
    """메인 함수"""
    manager = ServiceManager()
    
    def signal_handler(signum, frame):
        logger.info(f"\n🛑 Received signal {signum}")
        manager.stop_all_services()
        sys.exit(0)
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 인자에 따른 동작 선택
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'start':
            if manager.start_all_services():
                logger.info("🎉 All services started successfully!")
                manager.monitor_services()
            else:
                logger.error("❌ Failed to start all services")
                sys.exit(1)
        
        elif command == 'stop':
            manager.stop_all_services()
            logger.info("🛑 All services stopped")
        
        elif command == 'health':
            if manager.health_check_all():
                logger.info("✅ All services are healthy")
            else:
                logger.error("❌ Some services are unhealthy")
                sys.exit(1)
        
        elif command == 'status':
            manager.health_check_all()
        
        else:
            print(f"Unknown command: {command}")
            print("Usage: python run_all_services.py [start|stop|health|status]")
            sys.exit(1)
    
    else:
        # 기본 동작: 모든 서비스 시작 및 모니터링
        if manager.start_all_services():
            logger.info("🎉 All services started successfully!")
            manager.monitor_services()
        else:
            logger.error("❌ Failed to start all services")
            sys.exit(1)


if __name__ == "__main__":
    main() 