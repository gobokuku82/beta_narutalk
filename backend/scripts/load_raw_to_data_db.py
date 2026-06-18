"""Raw 일괄 적재 — data/{client}/raw/ 파일 → octormate_data `{client}._workspace`(layer='raw').

용도:
  - Internal source(orders·customers 등 8종, mock_api 없이 파일로만 존재)를 Postgres raw 로 부트스트랩.
  - External source 도 현 파일을 초기 적재(수집기가 이후 mock_api 로 갱신).
PostgresDataSource.get 이 이 raw 를 읽어 도구에 공급 → DATA_BACKEND=postgres e2e 의 입력 준비.

소형: FileDataSource.get(파싱) + PostgresWorkspace.save(blob) — 실제 코드 경로 재사용 → 형식 일치.
대형(STREAM_LIMIT 초과 .jsonl, 예: ga4 252MB): ds.stream_jsonl(한 줄씩) + ws.save_stream(배치 INSERT)
  → 메모리 일정한 "호스" 적재. 대형 non-jsonl 은 skip(현재 없음).

사용법:
    cd backend
    uv run python -m scripts.load_raw_to_data_db            # 전 client
    uv run python -m scripts.load_raw_to_data_db clumi      # 특정 client

Status: complete — 항목① raw 부트스트랩 + 대용량 스트리밍 (2026-06-07).
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.data_sources import SOURCE_REGISTRY, FileDataSource  # noqa: E402
from app.workspace.postgres import PostgresWorkspace  # noqa: E402

REPO_ROOT = project_root.parent          # backend/ → repo/
DATA_ROOT = REPO_ROOT / "data"
EXCLUDE = {"pipeline", "mock_api", "description"}  # client 아님
STREAM_LIMIT = 50 * 1024 * 1024          # 50MB 초과 .jsonl → 스트리밍(배치) 적재. 이하 → blob.


def discover_clients(arg: str | None) -> list[str]:
    if arg:
        return [arg]
    return [
        d.name
        for d in sorted(DATA_ROOT.iterdir())
        if d.is_dir() and d.name not in EXCLUDE and (d / "raw").is_dir()
    ]


def load_client(ds: FileDataSource, ws: PostgresWorkspace, client: str) -> tuple[int, int, int]:
    """(loaded, streamed, missing) 반환."""
    loaded = streamed = missing = 0
    for source_id, spec in sorted(SOURCE_REGISTRY.items()):
        if not ds.has(client, source_id):
            missing += 1
            continue
        raw_path = DATA_ROOT / client / "raw" / spec.filename
        size = raw_path.stat().st_size if raw_path.exists() else 0
        ext = raw_path.suffix.lower()
        try:
            if size > STREAM_LIMIT and ext == ".jsonl":
                # 대용량 jsonl → 한 줄씩 읽어 배치 적재 (메모리 일정)
                location = ws.save_stream(
                    "raw", spec.filename, ds.stream_jsonl(client, source_id), client=client
                )
                streamed += 1
                print(f"    [stream] {spec.filename:32s} ({size // (1024*1024)}MB) → {location}")
            elif size > STREAM_LIMIT:
                print(f"    [skip-big-nonjsonl] {client}/{spec.filename} ({size // (1024*1024)}MB)")
            else:
                data = ds.get(client, source_id)
                location = ws.save("raw", spec.filename, data, client=client)
                loaded += 1
                print(f"    [ok] {spec.filename:32s} → {location}")
        except Exception as e:
            print(f"    [err] {client}/{spec.filename}: {e}")
    return loaded, streamed, missing


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    print("=" * 60)
    print("OctorAD — Raw 적재 (data/{client}/raw → octormate_data raw)")
    print("=" * 60)

    clients = discover_clients(arg)
    print(f"[clients] {clients}\n")

    ds = FileDataSource(REPO_ROOT)
    ws = PostgresWorkspace()
    total_loaded = total_streamed = 0
    for client in clients:
        print(f"[{client}]")
        loaded, streamed, missing = load_client(ds, ws, client)
        total_loaded += loaded
        total_streamed += streamed
        print(f"    → blob {loaded}, streamed {streamed}, not-present {missing}\n")

    print(f"완료 — raw blob {total_loaded}건 + streamed {total_streamed}건 적재 (octormate_data).")


if __name__ == "__main__":
    main()
