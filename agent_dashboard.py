"""
Agent Execution Dashboard
Checkpointer 데이터를 읽어서 에이전트 실행 상태를 보여주는 대시보드
"""

import asyncio
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentDashboard:
    """에이전트 실행 상태 대시보드"""

    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)

    def list_agent_checkpoints(self) -> List[str]:
        """사용 가능한 에이전트 체크포인트 목록"""
        checkpoints = []
        if self.checkpoint_dir.exists():
            for db_file in self.checkpoint_dir.glob("**/*.db"):
                agent_name = db_file.stem
                checkpoints.append(agent_name)
        return checkpoints

    def read_checkpoint_data(self, agent_name: str) -> List[Dict[str, Any]]:
        """특정 에이전트의 체크포인트 데이터 읽기"""
        db_path = self.checkpoint_dir / agent_name / f"{agent_name}.db"

        if not db_path.exists():
            logger.warning(f"Checkpoint not found: {db_path}")
            return []

        results = []
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # checkpoints 테이블 읽기
            cursor.execute("""
                SELECT thread_id, checkpoint_ns, checkpoint_id, metadata, checkpoint, parent_checkpoint_id
                FROM checkpoints
                ORDER BY checkpoint_id DESC
                LIMIT 20
            """)

            rows = cursor.fetchall()
            for row in rows:
                thread_id, checkpoint_ns, checkpoint_id, metadata, checkpoint_data, parent_id = row

                # checkpoint 데이터 파싱
                checkpoint_info = {}
                if checkpoint_data:
                    try:
                        # Binary data를 JSON으로 파싱 시도
                        checkpoint_str = checkpoint_data.decode('utf-8') if isinstance(checkpoint_data, bytes) else checkpoint_data
                        checkpoint_info = json.loads(checkpoint_str) if checkpoint_str.startswith('{') else {"raw": checkpoint_str[:100]}
                    except:
                        checkpoint_info = {"binary_size": len(checkpoint_data)}

                # metadata 파싱
                metadata_info = {}
                if metadata:
                    try:
                        metadata_str = metadata.decode('utf-8') if isinstance(metadata, bytes) else metadata
                        metadata_info = json.loads(metadata_str) if metadata_str else {}
                    except:
                        metadata_info = {}

                results.append({
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": checkpoint_id,
                    "parent_id": parent_id,
                    "metadata": metadata_info,
                    "checkpoint_preview": checkpoint_info
                })

            conn.close()

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
        except Exception as e:
            logger.error(f"Error reading checkpoint: {e}")

        return results

    def read_writes_data(self, agent_name: str) -> List[Dict[str, Any]]:
        """writes 테이블에서 상태 업데이트 읽기"""
        db_path = self.checkpoint_dir / agent_name / f"{agent_name}.db"

        if not db_path.exists():
            return []

        results = []
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # writes 테이블 읽기
            cursor.execute("""
                SELECT thread_id, checkpoint_ns, checkpoint_id, task_id, channel, value
                FROM writes
                ORDER BY checkpoint_id DESC
                LIMIT 50
            """)

            rows = cursor.fetchall()
            for row in rows:
                thread_id, checkpoint_ns, checkpoint_id, task_id, channel, value = row

                # value 파싱
                value_info = {}
                if value:
                    try:
                        value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                        value_info = json.loads(value_str) if value_str.startswith('{') else {"raw": value_str[:100]}
                    except:
                        value_info = {"binary_size": len(value)}

                results.append({
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": checkpoint_id,
                    "task_id": task_id,
                    "channel": channel,
                    "value": value_info
                })

            conn.close()

        except Exception as e:
            logger.error(f"Error reading writes: {e}")

        return results

    def display_dashboard(self):
        """대시보드 출력"""
        print("\n" + "="*80)
        print(" AGENT EXECUTION DASHBOARD ".center(80))
        print("="*80)

        agents = self.list_agent_checkpoints()

        if not agents:
            print("\n[!] No agent checkpoints found")
            return

        print(f"\n[*] Found {len(agents)} agent(s) with checkpoints:")
        for agent in agents:
            print(f"    - {agent}")

        # 각 에이전트별 상태 표시
        for agent_name in agents:
            print(f"\n\n{'='*80}")
            print(f" {agent_name.upper()} ".center(80, '='))
            print("="*80)

            # Checkpoint 데이터
            checkpoints = self.read_checkpoint_data(agent_name)
            if checkpoints:
                print(f"\n[Checkpoints] Recent Checkpoints ({len(checkpoints)} found):")
                print("-"*60)

                for i, cp in enumerate(checkpoints[:5], 1):  # 최근 5개만 표시
                    print(f"\n[{i}] Thread: {cp['thread_id'][:8]}...")
                    print(f"    Checkpoint ID: {cp['checkpoint_id']}")

                    if cp.get('metadata'):
                        print(f"    Metadata: {json.dumps(cp['metadata'], indent=8)[:200]}")

                    if cp.get('checkpoint_preview'):
                        preview = str(cp['checkpoint_preview'])[:200]
                        print(f"    Data Preview: {preview}")

            # Writes 데이터
            writes = self.read_writes_data(agent_name)
            if writes:
                print(f"\n[State Updates] Recent State Updates ({len(writes)} found):")
                print("-"*60)

                # 채널별 그룹화
                channels = {}
                for write in writes:
                    channel = write['channel']
                    if channel not in channels:
                        channels[channel] = []
                    channels[channel].append(write)

                for channel, channel_writes in channels.items():
                    print(f"\n  Channel: {channel}")
                    for write in channel_writes[:3]:  # 채널당 3개만
                        value_preview = str(write['value'])[:100]
                        print(f"    - Task {write['task_id']}: {value_preview}")

    def analyze_execution_flow(self, agent_name: str, thread_id: Optional[str] = None):
        """특정 실행 플로우 분석"""
        print(f"\n\n{'='*80}")
        print(f" EXECUTION FLOW ANALYSIS: {agent_name} ".center(80))
        print("="*80)

        writes = self.read_writes_data(agent_name)

        if not writes:
            print("[!] No execution data found")
            return

        # thread_id별 그룹화
        threads = {}
        for write in writes:
            tid = write['thread_id']
            if thread_id and tid != thread_id:
                continue
            if tid not in threads:
                threads[tid] = []
            threads[tid].append(write)

        for tid, thread_writes in threads.items():
            print(f"\n\n[Thread] Thread: {tid[:16]}...")
            print("-"*60)

            # 실행 단계 추적
            steps = {}
            for write in thread_writes:
                channel = write['channel']
                value = write.get('value', {})

                # execution_step 추출
                if isinstance(value, dict) and 'execution_step' in value:
                    step = value['execution_step']
                    if step not in steps:
                        steps[step] = []
                    steps[step].append(value)

            if steps:
                print("\n[Steps] Execution Steps:")
                for step, step_data in steps.items():
                    print(f"  - {step}")

                    # 각 단계의 주요 데이터 표시
                    for data in step_data[:1]:  # 각 단계당 1개만
                        if isinstance(data, dict):
                            # status 표시
                            if 'status' in data:
                                print(f"      Status: {data['status']}")

                            # 통계 표시 (sales_analytics)
                            if 'statistics' in data and data['statistics']:
                                stats = data['statistics']
                                if 'total_sales' in stats:
                                    print(f"      Total Sales: {stats['total_sales']:,}원")
                                if 'transaction_count' in stats:
                                    print(f"      Transactions: {stats['transaction_count']}")

                            # insights 표시
                            if 'insights' in data and data['insights']:
                                print(f"      Insights: {len(data['insights'])} generated")
                                for insight in data['insights'][:2]:
                                    print(f"        - {insight}")

            # 최종 상태
            if thread_writes:
                last_write = thread_writes[0]  # 가장 최근
                if isinstance(last_write.get('value'), dict):
                    status = last_write['value'].get('status', 'unknown')
                    print(f"\n[Final] Final Status: {status}")


async def main():
    """메인 실행 함수"""
    dashboard = AgentDashboard()

    while True:
        print("\n" + "="*80)
        print(" AGENT DASHBOARD MENU ".center(80))
        print("="*80)
        print("\n1. Show Full Dashboard")
        print("2. Analyze Specific Agent")
        print("3. Analyze Specific Thread")
        print("4. Refresh")
        print("0. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            dashboard.display_dashboard()

        elif choice == "2":
            agents = dashboard.list_agent_checkpoints()
            if agents:
                print("\nAvailable agents:")
                for i, agent in enumerate(agents, 1):
                    print(f"  {i}. {agent}")

                try:
                    idx = int(input("\nSelect agent number: ")) - 1
                    if 0 <= idx < len(agents):
                        dashboard.analyze_execution_flow(agents[idx])
                except:
                    print("[!] Invalid selection")

        elif choice == "3":
            agent = input("Enter agent name: ").strip()
            thread = input("Enter thread ID (or press Enter for all): ").strip()
            dashboard.analyze_execution_flow(agent, thread if thread else None)

        elif choice == "4":
            print("[*] Refreshing...")
            continue

        elif choice == "0":
            print("\nExiting dashboard...")
            break

        else:
            print("[!] Invalid option")

        input("\n\nPress Enter to continue...")


if __name__ == "__main__":
    asyncio.run(main())