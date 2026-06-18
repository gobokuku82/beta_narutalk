# 세션 컴팩트 복구 — 2026-06-07

> 목적: 컨텍스트 압축 후 이어서 작업하기 위한 상태 박제.
> 이 세션 = **Postgres 기반 데이터 인프라 구축** (System DB 분리 + Data DB·콘솔 + 파이프라인→Postgres 이관 **항목①·② 완료**). 다음 = **활성화(`.env DATA_BACKEND=postgres`)** + P5 정합(선택).

---

## 0. 한 줄 요약

콘솔 2개(System/DB) + Postgres DB 2개(octormate_system / octormate_data, schema-per-client) 구축. 데이터 파이프라인의 **raw 읽기(항목①)·정제/계산 저장(항목②) 모두 Postgres로 전환 완료**. ABC+DI 관절 구현(PostgresWorkspace/PostgresDataSource) + lifespan 토글. 남은 건 **활성화(`.env DATA_BACKEND=postgres`)**.

---

## 1. 환경/접속 상태 ⚠️ (중요)

- **서버**: PostgreSQL `localhost:5432`, user `postgres`, pw `root1234`.
- **DB 3종**:
  - **`octormate_system`** = System DB (체크포인트 4테이블, 구조만 비움). `.env` CHECKPOINT_DB_URI가 이걸 가리킴. (이전 `adallpin`에서 전환)
  - **`octormate_data`** = Data DB. client별 schema: `clumi`(computed 39테이블 적재됨) · asyou/blooming/bluban(빈 schema) · `clumi._workspace`(파이프라인 항목② 산출 저장).
  - **`adallpin`** = 옛 System DB (데이터 보존, **미사용**. 원복하려면 .env만 되돌림).
- **`.env`**: `CHECKPOINT_DB_URI=...octormate_system`, `DATABASE_URL=...octormate_system`, **`DATA_BACKEND` 미설정(=file 기본)**. (gitignore — 커밋 안 됨)
- `settings.data_db_uri` (config 프로퍼티) = CHECKPOINT_DB_URI 자격증명 재사용 + db명만 octormate_data.
- **서버 시작**: `uv run python run_server_v2.py` (포트 **8001**). **프론트**: `cd frontend && npm run dev` (API 기본 localhost:8001).
- 셋업 스크립트: `python -m scripts.setup_checkpointer` (octormate_system), `python -m scripts.setup_data_db` (octormate_data + client schema + computed 적재).

---

## 2. 만든 것 (주요 커밋)

| 기능 | 위치 | 커밋 |
|---|---|---|
| DB 콘솔(범용, 후 System으로 개명) | `api_v2/routes/system_console.py` `/api/system`, FE `features/system_console` `/system` | 0ebbf33 · 64194ad(개명) |
| 설계/계획 문서 박제 | `docs/_claude/{memory,conversation,data}/*` (force-add 추적) | 5d3e0da |
| (viz 차트 — 사용자 불요로 revert) | — | fe4b9bd→92e7433 |
| **Data DB + /db 콘솔** | `scripts/setup_data_db.py` · `routes/data_console.py` `/api/data` · FE `features/data_console` `/db`(client selector) | dcd2163 |
| System DB 전환 adallpin→octormate_system | `.env` (로컬) | (커밋 없음) |
| **P1 PostgresWorkspace** | `app/data_pg_util.py` · `app/workspace/postgres.py` | 38eb9d2 |
| **항목② 토글** (정제/계산→Postgres) | `config.py DATA_BACKEND` · `api_v2/main.py` lifespan set_workspace | 3763211 |

콘솔 2개: **`/system`**(octormate_system, 체크포인트) · **`/db`**(octormate_data, client 데이터). 둘 다 표 보기/수정/삭제, SQL 0.

---

## 3. 핵심 결정 · 컨벤션 (이 세션 확정)

- **conversation = 기록(에피소드) / memory = 학습** (단어 분리). System(내부 DB) vs DB(client 데이터).
- **schema-per-client** (client = Postgres schema, 새 client = `data/{client}/computed/` 폴더 + setup 재실행 → 자동).
- **raw = JSONB(반정형) / cleaned·computed = 타입 테이블(정형)**. 둘 다 같은 Postgres.
- 저장 계층 **ABC + DI** (`WorkspaceBackend`/`DataSource` + `get_default_*()`/`set_*()`) → 구현 swap만으로 전체 전환. 도구·러너·YAML 불변.
- **`DATA_BACKEND`** env (file|postgres, 기본 file) = 안전 토글. postgres면 lifespan이 PostgresWorkspace로 swap.
- PostgresWorkspace 저장: `{client}._workspace(layer,key,payload jsonb)`=라운드트립 정확본 + `{client}.{layer}_{key}` 타입테이블=콘솔 표시.

---

## 4. 진행 중 — 데이터 파이프라인 파일→Postgres 이관

**계획서**: [docs/_claude/data/파이프라인_파일to postgres_이관_계획_2026-06-07.md](../_claude/data/파이프라인_파일to%20postgres_이관_계획_2026-06-07.md)

- **항목② (정제/계산 → Postgres)**: ✅ **완료**. `.env`에 `DATA_BACKEND=postgres` + 재시작이면 파이프라인이 cleaned/computed를 `octormate_data`에 저장. e2e 검증됨(promotion_revenue → `clumi._workspace`).
- **항목① (raw 수집 → Postgres)**: ✅ **완료 (2026-06-07)**. 커밋:
  1. **P2 `PostgresDataSource`** (`app/data_sources/postgres.py`, 1d24710): raw를 `{client}._workspace`(layer='raw')에서 읽어 확장자별 복원(.csv→DataFrame/.json→dict|list/.jsonl→list/.sql→str). 통합테스트 10 PASS.
  2. **P3 수집기 seam** (`tools/collection/_base.py`, bd370b1): `_fetch_from_mock_api` 백엔드 분기 — File=기존 복사+archive(불변) / 비파일=mock_api 파싱 후 `workspace.save("raw",...)`. seam 5 + file 회귀 55 PASS.
  3. **raw 적재** (`scripts/load_raw_to_data_db.py`, 25f69d4): data/{client}/raw 파일 → `octormate_data` raw 부트스트랩(internal 포함). clumi 26건 적재(ga4 2종 >50MB skip).
  4. **P4 토글** (`api_v2/main.py`, f349da2): lifespan에 `set_data_source(PostgresDataSource())` 추가(DATA_BACKEND=postgres 시). e2e 4 PASS(raw 읽기·정제/계산 쓰기 전부 Postgres).

---

## 5. 다음 세션 즉시 할 일

> 항목①·② **완료**. 파이프라인 영속화 파일→Postgres 이관 핵심(P1~P4) 끝. 남은 건 활성화·정합·확대뿐.

1. **활성화(미실행)**: `.env`에 `DATA_BACKEND=postgres` 추가 + 서버 재시작 → 입력 raw 읽기·출력 정제/계산 저장 모두 `octormate_data`. (현재 `DATA_BACKEND` 미설정=file 기본, 안전)
2. **활성화 후 검증**: 실제 에이전트 쿼리 1회 → `/db` 콘솔에서 clumi schema에 cleaned/computed 테이블 갱신 확인.
3. ~~**P5**: setup_data_db 테이블명 정합~~ ✅ **완료**: setup_data_db 를 PostgresWorkspace.save 경유로 재작성 → `computed_*` 일관 + `_workspace` 진실행. clumi legacy(prefix없음) 39→0. 이제 raw_*/cleaned_*/computed_*/_workspace 완전 일관.
4. **후속**: 전 client 확대, 수집기 seam 대용량 스트리밍, file 백엔드 폐기(전환 Sprint, [[feedback_no_mixed_codebases]]).
   - (완료) 대용량 raw 스트리밍 적재 — ga4 252MB/95MB Postgres 적재(`16bc314`). save_stream/stream_jsonl, peak 68MB(vs 바가지 1.3GB).
5. (환경갭) `test_save_parquet_load_roundtrip` = pyarrow 미설치로 fail — 항목① 무관. parquet 쓰려면 `uv add pyarrow`.

---

## 6. 포인터

- 설계: `docs/_claude/data/data_db_postgres_설계_2026-06-07.md`, `docs/_claude/conversation/대화_conversation_시스템_설계_2026-06-06.md`
- 코드 seam: `app/workspace/base.py`(ABC) · `app/workspace/postgres.py`(P1) · `app/data_pg_util.py`(헬퍼) · `app/data_sources/file.py`(SOURCE_REGISTRY) · `tools/collection/_base.py`(수집기)
- 콘솔: `api_v2/routes/{system_console,data_console}.py` · FE `features/{system_console,data_console}`
- ⚠️ 동시 다른 세션이 같은 repo `main`에 커밋 중일 수 있음 — 커밋은 경로 명시 원샷(`git add <files> && git commit -- <files>`).
