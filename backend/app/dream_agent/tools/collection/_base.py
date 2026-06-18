"""RawCollectorBase — 21 raw collector 의 공통 로직.

POC: DataSource 통한 thin wrapper. subclass 는 FILE_NO + PRODUCES_KEY 만 정의.
MVP+: 외부 API 호출로 _fetch_raw 만 override.

Step 4e (2026-05-27): load_clumi_source 직접 호출 제거 → self.ds.get(client, source_id).
②-a (2026-05-30): clumi_loader 의존 제거 — file_no → source_id 매핑 자체 보유.
                  FILE_NO 는 21 subclass 호환 유지 (clumi POC 결합 — MVP+ 시 subclass 가 SOURCE_ID 정의로 마이그레이션).
⑵ (2026-06-01): collector 2종류 분리 박제 (사용자 의도, ADR-027 권한 정합).
                External = mock_api → raw 수집 + 읽기 / Internal = raw 직접 읽기.
                external/ 13 = ExternalRawCollectorBase, internal/ 8 = InternalRawCollectorBase.
                MVP+ 시 ExternalRawCollectorBase._fetch_from_mock_api 를 실 API SDK 호출로 swap.
⑶ (2026-06-01): Pre-overwrite archive 추가 (사용자 Y 옵션).
                mock_api 파일이 raw 보다 새로우면 → raw_history/{timestamp}/ 으로 archive 후 새 raw 진입.
                자동 갱신 감지 (mtime 비교, 사용자 결정 0). 평소 idempotent skip 유지.
                MVP+ 진화: S3 / Glacier tier 로 swap, manifest.json 박제.
"""
from __future__ import annotations
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool

logger = get_logger(__name__)

# _base.py → collection(0) tools(1) dream_agent(2) app(3) backend(4) repo(5).
# Postgres 백엔드(self.ds 에 repo_root 없음)일 때 mock_api 위치 유도용.
_REPO_ROOT = Path(__file__).resolve().parents[5]


def _parse_raw_file(path: Path) -> Any:
    """mock_api 파일을 FileDataSource.get 과 동일 규약으로 파싱 (Postgres raw 적재용).

    .csv→DataFrame / .json→dict|list / .jsonl→list[dict] / .sql→str.
    PostgresWorkspace.save 가 jsonable 직렬화 → PostgresDataSource.get 이 동일 타입 복원.
    """
    suffix = path.suffix.lower()
    if suffix == ".csv":
        import pandas as pd

        return pd.read_csv(path, encoding="utf-8-sig")
    if suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if suffix == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    if suffix == ".sql":
        return path.read_text(encoding="utf-8")
    raise ValueError(f"unsupported raw extension: {suffix}")


# clumi POC 호환 — legacy file_no(1~21) → DataSource semantic source_id 매핑.
# subclass 는 FILE_NO 만 정의하면 본 base 가 source_id 로 변환.
_FILE_NO_TO_SOURCE_ID: dict[int, str] = {
    1:  "meta_ads_performance",
    2:  "meta_ads_by_age",
    3:  "meta_instagram_inapp",
    4:  "naver_searchad",
    5:  "orders",
    6:  "customers",
    7:  "ga4_traffic_source",
    8:  "ga4_page_events",
    9:  "signup_events",
    10: "customer_rfm",
    11: "promotions",
    12: "category_sales",
    13: "naver_interest_alert",
    14: "instagram_engagement",
    15: "naver_advoost",
    16: "kakao_bizmessage",
    17: "naver_talktalk",
    18: "crm_messages",
    19: "household_structure",
    20: "ad_change_history",
    21: "grade_history",
}


class RawCollectorBase(BaseTool):
    """공통 collector base — subclass 가 FILE_NO·PRODUCES_KEY 정의.

    Attributes:
        FILE_NO: int — clumi POC legacy file_no (1~21). _FILE_NO_TO_SOURCE_ID 로 변환.
        PRODUCES_KEY: str — 다음 tool 의 입력 키
    """
    FILE_NO: int = 0
    PRODUCES_KEY: str = "raw"

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        source_id = _FILE_NO_TO_SOURCE_ID.get(self.FILE_NO, "")
        if not source_id:
            raise ValueError(f"FILE_NO={self.FILE_NO} 의 source_id 매핑 없음")

        data = self.ds.get(context.client_id, source_id)  # count 용 일시 적재 (반환 안 함 → GC)

        # 행수 추정 (DataFrame·list·dict·str)
        if hasattr(data, "__len__"):
            count = len(data)
        elif isinstance(data, dict):
            count = len(data.get("data", [])) if "data" in data else 1
        else:
            count = 1

        # L4 (2026-06-11, 계획_L4_collector참조반환): 데이터셋은 결과에 *비탑재* — 참조만 반환.
        # 과거 "{PRODUCES_KEY: data}" 통째 반환이 state→checkpoint 암묵 저장으로 104MB/턴 누수
        # (소비자 0 — downstream 은 self.ds.get/stream_jsonl 로 데이터 평면에서 직접 읽음.
        #  유일한 raw 체인인 ReviewCollector 는 본 base 밖.) 키는 truthy dict 로 유지(존재성 호환).
        # 근거: docs/reports/근본원인_execution_state_raw누수_2026-06-11.md §7 전수 감사.
        logger.info(
            "raw_collector",
            tool=self.spec.name,
            file_no=self.FILE_NO,
            source_id=source_id,
            client=context.client_id,
            count=count,
        )

        return {
            self.PRODUCES_KEY: {
                "_dataref": True,
                "source_id": source_id,
                "layer": "raw",
                "count": count,
                "where": "data 레이어에서 self.ds.get/stream_jsonl 로 조회 (결과 비탑재 정책)",
            },
            "count": count,
            "file_no": self.FILE_NO,
            "source_id": source_id,
            "_meta": {"params": self.merge_params(params)},
        }


class InternalRawCollectorBase(RawCollectorBase):
    """내부 collector — data/{client}/raw/ 에서 직접 읽기. 수집 행위 X.

    권한 (ADR-027): 내부 raw 읽기 only. mock_api / 외부 API 접근 금지.
    적용: collection/internal/ 8 collector (orders/customers/customer_rfm/grade_history/
                                            signup_events/promotions/category_sales/crm_messages).
    """
    pass


class ExternalRawCollectorBase(RawCollectorBase):
    """외부 collector — mock_api (POC) / 실 API (MVP+) → raw 저장 + 읽기.

    권한 (ADR-027): 외부 source 수집 + 내부 raw 저장 + 읽기.
    POC: data/mock_api/{client}/clumi_mock_NN_{stem}.{ext} → data/{client}/raw/{filename}
    MVP+: _fetch_from_mock_api 를 실 API SDK 호출로 swap (override).
    적용: collection/external/ 13 collector (meta/naver/kakao/ga4/instagram/household/ad_change).
    """

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        source_id = _FILE_NO_TO_SOURCE_ID.get(self.FILE_NO, "")
        if source_id:
            self._fetch_from_mock_api(context.client_id, source_id)
        return await super().execute(params, context)

    def _fetch_from_mock_api(self, client: str, source_id: str) -> None:
        """외부 수집 (POC) — mock_api → raw 저장. 백엔드 무관(파일/Postgres) 동작.

        매핑 컨벤션: data/mock_api/{client}/clumi_mock_*_{raw_stem}.{ext}
        백엔드 분기 (R4, 2026-06-07):
          - File (self.ds 에 repo_root) → 기존 파일 복사 + raw_history archive (mtime idempotent)
          - Postgres 등 → mock_api 파싱 후 workspace.save("raw", filename) (upsert)
        mock_api 파일은 양쪽 모두 디스크에 있음 → repo_root 는 self.ds 우선, 없으면 모듈서 유도.
        """
        from app.data_sources.file import SOURCE_REGISTRY

        spec = SOURCE_REGISTRY.get(source_id)
        if not spec:
            return

        repo_root = getattr(self.ds, "repo_root", None) or _REPO_ROOT
        mock_dir = repo_root / "data" / "mock_api" / client
        if not mock_dir.exists():
            return

        raw_filename = Path(spec.filename)
        raw_stem = raw_filename.stem
        ext = raw_filename.suffix
        candidates = [
            p for p in mock_dir.glob(f"clumi_mock_*_{raw_stem}{ext}")
            if p.stem.endswith(f"_{raw_stem}")
        ]
        if not candidates:
            return
        mock_path = candidates[0]

        if hasattr(self.ds, "repo_root"):
            self._fetch_to_file(client, source_id, spec.filename, mock_path)
        else:
            self._fetch_to_workspace(client, source_id, spec.filename, mock_path)

    def _fetch_to_file(self, client: str, source_id: str, filename: str, mock_path: Path) -> None:
        """File 백엔드 — mock_api → data/{client}/raw/ 복사 + 갱신 시 raw_history archive.

        raw 있고 mock_api 안 새로움 → skip (idempotent).
        raw 있고 mock_api 더 새로움 → raw_history/{ts}/ archive 후 새 raw 복사.
        Archive: data/{client}/raw_history/{YYYY-MM-DD_HH-MM-SS}/{filename}
        """
        raw_path = self.ds.repo_root / "data" / client / "raw" / filename

        if raw_path.exists():
            if mock_path.stat().st_mtime <= raw_path.stat().st_mtime:
                return  # mock_api 안 새로움 → skip (idempotent)
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            archive_path = self.ds.repo_root / "data" / client / "raw_history" / ts / filename
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(raw_path), str(archive_path))
            logger.info(
                "external_raw_collector.archive",
                tool=self.spec.name, client=client, source_id=source_id,
                archived_to=str(archive_path),
            )

        raw_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mock_path, raw_path)
        logger.info(
            "external_raw_collector.fetch",
            tool=self.spec.name, client=client, source_id=source_id,
            backend="file", mock_path=str(mock_path), raw_path=str(raw_path),
        )

    def _fetch_to_workspace(self, client: str, source_id: str, filename: str, mock_path: Path) -> None:
        """Postgres 등 비-파일 백엔드 — mock_api 파싱 후 workspace.save("raw", filename) (upsert).

        get_default_workspace() = 현 설치된 백엔드(lifespan 에서 PostgresWorkspace 로 swap).
        PostgresWorkspace.save 가 {client}._workspace(layer='raw') upsert + 표시용 타입테이블.
        """
        from app.workspace import get_default_workspace

        parsed = _parse_raw_file(mock_path)
        location = get_default_workspace().save("raw", filename, parsed, client=client)
        logger.info(
            "external_raw_collector.fetch",
            tool=self.spec.name, client=client, source_id=source_id,
            backend="workspace", mock_path=str(mock_path), location=location,
        )


__all__ = ["RawCollectorBase", "InternalRawCollectorBase", "ExternalRawCollectorBase"]
