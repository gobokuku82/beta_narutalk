"""
토큰 사용량 추적 및 비용 관리
실시간 모니터링 및 알림 기능
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)

class TokenTracker:
    """토큰 사용량 추적 클래스"""

    def __init__(self, alert_threshold: Optional[Dict[str, int]] = None):
        """
        Args:
            alert_threshold: 알림 임계값 설정
                예: {"daily": 100000, "hourly": 10000}
        """
        # 사용량 데이터
        self.usage_data = defaultdict(lambda: defaultdict(int))
        self.usage_history = []

        # 비용 설정 (1K 토큰당 USD)
        self.pricing = {
            "gpt-4o": {
                "input": 0.0025,
                "output": 0.01
            },
            "gpt-4o-mini": {
                "input": 0.00015,
                "output": 0.0006
            },
            "gpt-4-turbo": {
                "input": 0.01,
                "output": 0.03
            }
        }

        # 알림 임계값
        self.alert_threshold = alert_threshold or {
            "daily": 500000,  # 일일 50만 토큰
            "hourly": 50000,   # 시간당 5만 토큰
            "per_request": 10000  # 요청당 1만 토큰
        }

        # 알림 히스토리
        self.alerts_sent = []

        # 세션 시작 시간
        self.session_start = datetime.now()

    def track(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        토큰 사용량 추적

        Args:
            model: 사용된 모델명
            prompt_tokens: 입력 토큰 수
            completion_tokens: 출력 토큰 수
            category: 사용 카테고리
            user_id: 사용자 ID
            metadata: 추가 메타데이터

        Returns:
            추적 결과
        """
        timestamp = datetime.now()
        total_tokens = prompt_tokens + completion_tokens

        # 사용량 기록
        record = {
            "timestamp": timestamp.isoformat(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "category": category,
            "user_id": user_id,
            "metadata": metadata or {},
            "cost": self._calculate_cost(model, prompt_tokens, completion_tokens)
        }

        # 히스토리에 추가
        self.usage_history.append(record)

        # 집계 데이터 업데이트
        self._update_aggregates(record)

        # 임계값 확인
        alerts = self._check_thresholds(record)
        if alerts:
            self._send_alerts(alerts)

        logger.debug(f"Tracked {total_tokens} tokens for {model} in {category}")

        return {
            "record": record,
            "alerts": alerts,
            "current_stats": self.get_current_stats()
        }

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """비용 계산"""
        # 모델명에서 기본 모델 추출
        base_model = None
        for key in self.pricing.keys():
            if key in model.lower():
                base_model = key
                break

        if not base_model:
            # 기본값 사용
            base_model = "gpt-4o"

        pricing = self.pricing[base_model]
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]

        return round(input_cost + output_cost, 6)

    def _update_aggregates(self, record: Dict):
        """집계 데이터 업데이트"""
        timestamp = datetime.fromisoformat(record["timestamp"])

        # 시간별 집계
        hour_key = timestamp.strftime("%Y-%m-%d %H:00")
        self.usage_data["hourly"][hour_key] += record["total_tokens"]

        # 일별 집계
        day_key = timestamp.strftime("%Y-%m-%d")
        self.usage_data["daily"][day_key] += record["total_tokens"]

        # 모델별 집계
        self.usage_data["by_model"][record["model"]] += record["total_tokens"]

        # 카테고리별 집계
        if record["category"]:
            self.usage_data["by_category"][record["category"]] += record["total_tokens"]

        # 사용자별 집계
        if record["user_id"]:
            self.usage_data["by_user"][record["user_id"]] += record["total_tokens"]

        # 총 비용
        self.usage_data["total_cost"]["usd"] += record["cost"]

    def _check_thresholds(self, record: Dict) -> List[Dict]:
        """임계값 확인"""
        alerts = []
        timestamp = datetime.fromisoformat(record["timestamp"])

        # 요청당 토큰 확인
        if record["total_tokens"] > self.alert_threshold.get("per_request", float('inf')):
            alerts.append({
                "type": "per_request",
                "message": f"Single request used {record['total_tokens']} tokens",
                "severity": "warning"
            })

        # 시간별 토큰 확인
        hour_key = timestamp.strftime("%Y-%m-%d %H:00")
        hourly_total = self.usage_data["hourly"][hour_key]
        if hourly_total > self.alert_threshold.get("hourly", float('inf')):
            alerts.append({
                "type": "hourly",
                "message": f"Hourly usage reached {hourly_total} tokens",
                "severity": "warning"
            })

        # 일별 토큰 확인
        day_key = timestamp.strftime("%Y-%m-%d")
        daily_total = self.usage_data["daily"][day_key]
        if daily_total > self.alert_threshold.get("daily", float('inf')):
            alerts.append({
                "type": "daily",
                "message": f"Daily usage reached {daily_total} tokens",
                "severity": "critical"
            })

        return alerts

    def _send_alerts(self, alerts: List[Dict]):
        """알림 전송"""
        for alert in alerts:
            # 중복 알림 방지
            alert_key = f"{alert['type']}:{datetime.now().strftime('%Y-%m-%d %H')}"
            if alert_key not in self.alerts_sent:
                logger.warning(f"Token usage alert: {alert['message']}")
                self.alerts_sent.append(alert_key)

                # 실제 환경에서는 이메일, 슬랙 등으로 알림 전송
                # self._send_notification(alert)

    def get_current_stats(self) -> Dict[str, Any]:
        """현재 통계 반환"""
        now = datetime.now()
        current_hour = now.strftime("%Y-%m-%d %H:00")
        current_day = now.strftime("%Y-%m-%d")

        return {
            "session": {
                "duration": str(now - self.session_start),
                "total_requests": len(self.usage_history)
            },
            "tokens": {
                "hourly": self.usage_data["hourly"].get(current_hour, 0),
                "daily": self.usage_data["daily"].get(current_day, 0),
                "total": sum(r["total_tokens"] for r in self.usage_history)
            },
            "cost": {
                "total_usd": round(self.usage_data["total_cost"]["usd"], 2),
                "hourly_usd": self._get_hourly_cost(),
                "daily_usd": self._get_daily_cost()
            },
            "by_model": dict(self.usage_data["by_model"]),
            "by_category": dict(self.usage_data["by_category"])
        }

    def _get_hourly_cost(self) -> float:
        """현재 시간 비용"""
        current_hour = datetime.now().strftime("%Y-%m-%d %H:00")
        hourly_records = [
            r for r in self.usage_history
            if datetime.fromisoformat(r["timestamp"]).strftime("%Y-%m-%d %H:00") == current_hour
        ]
        return round(sum(r["cost"] for r in hourly_records), 2)

    def _get_daily_cost(self) -> float:
        """오늘 비용"""
        current_day = datetime.now().strftime("%Y-%m-%d")
        daily_records = [
            r for r in self.usage_history
            if datetime.fromisoformat(r["timestamp"]).strftime("%Y-%m-%d") == current_day
        ]
        return round(sum(r["cost"] for r in daily_records), 2)

    def get_usage_report(self, period: str = "daily") -> Dict[str, Any]:
        """사용량 보고서 생성"""
        if period == "hourly":
            return self._get_hourly_report()
        elif period == "daily":
            return self._get_daily_report()
        else:
            return self._get_full_report()

    def _get_hourly_report(self) -> Dict[str, Any]:
        """시간별 보고서"""
        last_24_hours = []
        now = datetime.now()

        for i in range(24):
            hour = now - timedelta(hours=i)
            hour_key = hour.strftime("%Y-%m-%d %H:00")
            last_24_hours.append({
                "hour": hour_key,
                "tokens": self.usage_data["hourly"].get(hour_key, 0)
            })

        return {
            "period": "last_24_hours",
            "data": list(reversed(last_24_hours)),
            "total": sum(h["tokens"] for h in last_24_hours)
        }

    def _get_daily_report(self) -> Dict[str, Any]:
        """일별 보고서"""
        last_7_days = []
        now = datetime.now()

        for i in range(7):
            day = now - timedelta(days=i)
            day_key = day.strftime("%Y-%m-%d")
            last_7_days.append({
                "date": day_key,
                "tokens": self.usage_data["daily"].get(day_key, 0)
            })

        return {
            "period": "last_7_days",
            "data": list(reversed(last_7_days)),
            "total": sum(d["tokens"] for d in last_7_days)
        }

    def _get_full_report(self) -> Dict[str, Any]:
        """전체 보고서"""
        return {
            "summary": self.get_current_stats(),
            "hourly": self._get_hourly_report(),
            "daily": self._get_daily_report(),
            "top_users": self._get_top_users(),
            "top_categories": self._get_top_categories()
        }

    def _get_top_users(self, limit: int = 10) -> List[Dict]:
        """상위 사용자"""
        user_usage = self.usage_data["by_user"]
        sorted_users = sorted(user_usage.items(), key=lambda x: x[1], reverse=True)
        return [
            {"user_id": user, "tokens": tokens}
            for user, tokens in sorted_users[:limit]
        ]

    def _get_top_categories(self, limit: int = 10) -> List[Dict]:
        """상위 카테고리"""
        category_usage = self.usage_data["by_category"]
        sorted_categories = sorted(category_usage.items(), key=lambda x: x[1], reverse=True)
        return [
            {"category": cat, "tokens": tokens}
            for cat, tokens in sorted_categories[:limit]
        ]

    def export_history(self, filepath: str):
        """히스토리 내보내기"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "session_start": self.session_start.isoformat(),
                "export_time": datetime.now().isoformat(),
                "history": self.usage_history,
                "aggregates": {
                    k: dict(v) for k, v in self.usage_data.items()
                }
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"Usage history exported to {filepath}")

    def reset(self):
        """추적 데이터 초기화"""
        self.usage_data.clear()
        self.usage_history.clear()
        self.alerts_sent.clear()
        self.session_start = datetime.now()
        logger.info("Token tracker reset")