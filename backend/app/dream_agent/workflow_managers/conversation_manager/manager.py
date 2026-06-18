"""ConversationManager — 대화(turn) 조회 전용 (checkpoint 읽기).

설계: docs/reports/대화이력_설계_단계적_2026-06-09.md §7.
대화(conversation) 경로 전담 — 메모리(MemoryManager)와 **분리**(저장소·매니저로 구분).
LangGraph checkpoint(octormate_system)를 읽어 과거 turn을 conversation_id로 묶어 반환.

식별: thread_id="{conversation_id}_{turn_id}" 인데 실제 ID에 접두사/`_`가 있어
parse_thread_id는 부정확 → **state 안의 conversation_id/turn_id 필드를 직접 사용**.

Status: partial — Phase 1 (목록·turns 조회, read-only). 회상(recall)·conversations 테이블은 후속(P2/P3).
"""
from __future__ import annotations

import re
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_TITLE_MAX = 40
_PREVIEW_MAX = 90


def _clean(text: str) -> str:
    """마크다운 마커 제거 후 1줄 요약용 정리."""
    t = re.sub(r"[#*`>]", "", text or "")
    return re.sub(r"\s+", " ", t).strip()


def _title(cv: dict) -> str:
    """Phase 1 제목 = 첫 질문 truncate. (AI 요약 제목은 후속)"""
    q = (cv.get("user_input") or "").strip()
    return q[:_TITLE_MAX] + ("…" if len(q) > _TITLE_MAX else "")


def _preview(cv: dict) -> str:
    resp = cv.get("response") or {}
    text = _clean(resp.get("text") or resp.get("summary") or "")
    return text[:_PREVIEW_MAX] + ("…" if len(text) > _PREVIEW_MAX else "")


def _status(cv: dict) -> str:
    """정확한 상태 — 응답=완료 / 에러=오류 / terminal신호=오류·취소 / 그 외=미완료.

    '진행 중(active)'은 정적 조회로 단정 불가 → 응답·에러 없으면 '미완료(incomplete)'.
    (멍청아처럼 응답 없는 턴을 '진행 중'으로 오표기하던 것 정정)
    """
    if cv.get("error"):
        return "error"
    if cv.get("response"):
        return "completed"
    overall = str((cv.get("execution_result") or {}).get("overall_status") or "").lower()
    if any(k in overall for k in ("fail", "halt", "error")):
        return "error"
    if any(k in overall for k in ("cancel", "abort")):
        return "cancelled"
    return "incomplete"


def _messages(cv: dict) -> list[dict]:
    """turn → 채팅 메시지 배열 (프론트 ChatMessage 형태: 텍스트/슬라이드/다운로드 재현)."""
    msgs: list[dict] = []
    if cv.get("user_input"):
        msgs.append({"role": "user", "content": cv["user_input"]})
    resp = cv.get("response") or {}
    if resp:
        msgs.append(
            {
                "role": "assistant",
                "content": resp.get("text") or "",
                "format": resp.get("format"),
                "attachments": resp.get("attachments") or [],
            }
        )
    return msgs


class ConversationManager:
    """checkpoint(대화 turn 상태)를 읽어 대화이력을 조립. MemoryManager(메모리)와 분리."""

    def __init__(self, checkpointer: Any, db_pool: Any) -> None:
        self._cp = checkpointer  # AsyncPostgresSaver (app.state.checkpointer)
        self._pool = db_pool  # asyncpg pool on octormate_system (app.state.db_pool)

    async def _load_latest_states(self) -> list[dict]:
        """모든 thread의 최신 state. 실제 agent turn만(테스트 thread 제외).

        N+1(thread당 aget_tuple 1회) — POC 소량 기준. 대량이면 Phase 2(conversations 테이블).
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT DISTINCT thread_id FROM checkpoints")
        out: list[dict] = []
        for r in rows:
            tid = r["thread_id"]
            try:
                tup = await self._cp.aget_tuple({"configurable": {"thread_id": tid}})
            except Exception as e:  # noqa: BLE001
                logger.warning("aget_tuple failed", thread_id=tid, error=str(e))
                continue
            if not tup:
                continue
            cv = tup.checkpoint.get("channel_values", {}) or {}
            # 실제 agent turn만: conversation_id + user_input 보유 (테스트 thread 제외)
            if not cv.get("conversation_id") or not cv.get("user_input"):
                continue
            out.append({"cv": cv, "ts": tup.checkpoint.get("ts"), "thread_id": tid})
        return out

    async def list_conversations(
        self, client: str | None = None, limit: int = 20, offset: int = 0
    ) -> dict:
        """대화 목록 (conversation_id로 그룹핑, 최신순)."""
        states = await self._load_latest_states()
        if client:
            states = [s for s in states if s["cv"].get("client_id") == client]

        groups: dict[str, list[dict]] = {}
        for s in states:
            groups.setdefault(s["cv"]["conversation_id"], []).append(s)

        items: list[dict] = []
        for cid, turns in groups.items():
            turns.sort(key=lambda s: s["ts"] or "")
            first, last = turns[0]["cv"], turns[-1]["cv"]
            items.append(
                {
                    "conversation_id": cid,
                    "title": _title(first),
                    "preview": _preview(last),
                    "turn_count": len(turns),
                    "status": _status(last),
                    "updated_at": turns[-1]["ts"],
                    "client_id": last.get("client_id"),
                }
            )
        items.sort(key=lambda x: x["updated_at"] or "", reverse=True)
        total = len(items)
        return {
            "items": items[offset : offset + limit],
            "total": total,
            "has_more": offset + limit < total,
        }

    async def get_turns(self, conversation_id: str) -> dict:
        """한 대화의 turn(메시지) 목록 — 채팅 복원용.

        ★ 그 대화의 thread만 로드(전체 스캔 X) → 복원 속도 개선.
        thread_id = "{conversation_id}_{turn_id}" 이므로 prefix 로 그 대화 thread만 추림.
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT DISTINCT thread_id FROM checkpoints")
        prefix = conversation_id + "_"
        tids = [r["thread_id"] for r in rows if r["thread_id"].startswith(prefix)]

        turns: list[dict] = []
        for tid in tids:
            try:
                tup = await self._cp.aget_tuple({"configurable": {"thread_id": tid}})
            except Exception as e:  # noqa: BLE001
                logger.warning("aget_tuple failed", thread_id=tid, error=str(e))
                continue
            if not tup:
                continue
            cv = tup.checkpoint.get("channel_values", {}) or {}
            if cv.get("conversation_id") != conversation_id:  # prefix 오매칭 안전장치
                continue
            turns.append({"cv": cv, "ts": tup.checkpoint.get("ts")})

        turns.sort(key=lambda s: s["ts"] or "")
        items = [
            {
                "turn_id": s["cv"].get("turn_id"),
                "messages": _messages(s["cv"]),
                "status": _status(s["cv"]),
                "created_at": s["ts"],
            }
            for s in turns
        ]
        return {"conversation_id": conversation_id, "items": items, "total": len(items)}

    async def delete_conversation(self, conversation_id: str) -> dict:
        """대화 삭제 — 해당 conversation의 모든 turn checkpoint 제거.

        checkpoints/checkpoint_blobs/checkpoint_writes 에서 thread_id 일괄 삭제.
        (Phase 1: checkpoint만. 첨부파일 outputs/ 정리는 후속 §9.) 되돌릴 수 없음.
        """
        states = await self._load_latest_states()
        tids = [
            s["thread_id"]
            for s in states
            if s["cv"].get("conversation_id") == conversation_id
        ]
        if not tids:
            return {"conversation_id": conversation_id, "deleted_threads": 0}
        async with self._pool.acquire() as conn:
            # 테이블명은 리터럴 상수(사용자 입력 아님), thread_id 는 바인딩.
            for table in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
                await conn.execute(
                    f"DELETE FROM {table} WHERE thread_id = ANY($1::text[])", tids
                )
        logger.info(
            "conversation deleted", conversation_id=conversation_id, threads=len(tids)
        )
        return {"conversation_id": conversation_id, "deleted_threads": len(tids)}
