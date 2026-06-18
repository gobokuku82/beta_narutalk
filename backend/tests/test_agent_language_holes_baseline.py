"""복합쿼리 §2.2 구멍 — 현 시스템 baseline 특성화 테스트 (그룹A, 결정론·무LLM).

계획서: docs/_claude/4layer_system/agent_language_test_plan_260606_v1.md §2 Track D.
검증: wivldm5do (4 적대 렌즈) → 본 테스트가 "종이 주장"을 *측정된 사실*로 확정.

**성격 = 특성화(characterization) 테스트.** 현재의 (대부분 깨진) 동작을 *통과하는*
assert 로 박제한다. PASS = "그 구멍이 현재 이렇게 동작함을 사실로 확인". 재설계/P0
수정 시 해당 동작이 바뀌면 이 테스트가 빨개지며 = 그게 의도된 변화 신호.

다루는 테스트 (그룹A, LLM 불요):
  D1 — shim 다의도 1:1 축소 + 역설 (reviews 가 diagnose 를 sentiment 로 뒤집음)
  D2 — operation 스칼라 천장 (아키텍처 사실, 강등)
  D3 — artifact 키 충돌 (first-match 마스킹; 메타데이터 vs 의미론 구분)
  D4 — report_writer silent-COMPLETE (게이트가 consumes 미선언이라 못 잡음) + 3중 drift + orphan
  D7 — quantifier ALL 자동전개 주체 부재 (Intent 에 quantifier 필드 없음)
  D8 — dashboard ref 입력경로 부재 (cognitive 가 대시보드 상태를 안 읽음)

각 테스트는 계획서 §2 의 "반증 시나리오"도 함께 검사 — 예측이 틀리면 그 자리에서 빨개진다.
"""
from __future__ import annotations

from app.dream_agent.cognitive.cognitive_stage import prepare_cognitive_prompt
from app.dream_agent.cognitive.intent_shim import intent_to_tasks
from app.dream_agent.execution.agent_pool import get_agent_pool
from app.dream_agent.execution.data_gate import check_consume_sufficiency
from app.dream_agent.response.responder import build_insufficient_data_payload
from app.dream_agent.schemas.execution_result import ExecutionResult, TodoResult, TodoStatus
from app.dream_agent.schemas.structured_query import Intent, TaskType
from app.dream_agent.tools.shared.helpers import find_in_previous


def _ids(intent: Intent) -> list[TaskType]:
    return [t.id for t in intent_to_tasks(intent)]


def _todo(tid: str, tool: str, status: TodoStatus, data: dict) -> TodoResult:
    return TodoResult(
        todo_id=tid, task_type="x", tool=tool, agent="a", status=status,
        data=data, started_at=0.0, ended_at=0.0, duration_ms=0.0,
    )


_INSUF = {"reason": "data_insufficient", "artifact": "raw_reviews", "detail": "raw_reviews 0건"}


# ════════════════════════════════════════════════════════════════════
# D1 — shim 다의도 1:1 축소 + 역설  (§2.2 D / 복합분석 붕괴2·5)
#   FAIL(=구멍 확정) iff: 5겹 의도가 단일 [SENTIMENT_ANALYSIS] 로 뭉개짐
#                        AND control(reviews 없는 diagnose)는 []로 degrade.
#   반증: reviews 포함에도 ≥2 task 반환하면 "1:1 축소" 가설 폐기.
# ════════════════════════════════════════════════════════════════════

def test_d1_five_fold_intent_collapses_to_single_sentiment():
    """관찰된 사실: 5겹 의도가 단일 sentiment task 하나로 환원된다.

    검증(wbvbfeoys) qualifier: 이건 reviews 우선규칙①(intent_shim.py:8 "operation 무관·
    최우선")의 *by-design* 출력이다 — "버그"인지 "설계"인지는 가치판단(코퍼스로 판단).
    이 테스트가 박제하는 *사실*은 "다의도가 단일 task 로 환원돼 diagnose/breakdown 등이
    tasks 에서 사라진다"는 것. 표현 천장 *자체*는 D2(operation 스칼라)가 입증 — D1 은 그 증상 한 사례.
    """
    five_fold = Intent(
        operation="diagnose",                       # ① 진단
        domain=["sales", "ad_performance", "reviews"],  # ② 매출 ③ 광고 ⑤ 리뷰
        metric=["roas", "revenue"],
        dimensions=["channel", "creative"],         # ④ 채널/소재 분해
    )
    # 5겹인데 단 하나로. (reviews 가 operation·domain 나머지를 전부 삼킴)
    assert _ids(five_fold) == [TaskType.SENTIMENT_ANALYSIS]
    # 반증 체크: 만약 ≥2 였다면 위 assert 가 깨지며 가설 폐기됨.


def test_d1_paradox_reviews_flips_diagnose_into_sentiment():
    """관찰된 사실: 'reviews' 유무가 같은 diagnose 의 tasks 를 가른다 (다의도 소멸 역설).

    control(reviews 없음) → diagnose 는 causal_analysis (2026-06-10 분석레이어 v2 — 실제 진단,
        구 [] degrade 해소). treatment(reviews 추가) → 같은 diagnose 가 [SENTIMENT_ANALYSIS] (규칙① reviews 최우선).
    역설(잔존): 리뷰가 붙으면 진단(causal) 의도가 감성으로 *뒤집혀 소멸* — operation 스칼라/domain 우선의
        영향(S1 sub_intents 가 근본 해소 대상). 여기선 그 *사실*을 박제.
    """
    control = Intent(operation="diagnose", domain=["sales"])             # 리뷰 없음
    treatment = Intent(operation="diagnose", domain=["sales", "reviews"])  # 리뷰 추가

    assert _ids(control) == [TaskType.CAUSAL_ANALYSIS]       # 실제 진단 (구 [] degrade 해소)
    assert _ids(treatment) == [TaskType.SENTIMENT_ANALYSIS]  # 진단이 감성분석으로 뒤집힘 (역설 잔존)


# ════════════════════════════════════════════════════════════════════
# D2 — operation 스칼라 천장  (§2.2 A / 붕괴1) — 아키텍처 사실(강등)
#   behavioral 테스트 아님 — 스키마 사실. D1·L1 이 그 *영향*을 측정.
# ════════════════════════════════════════════════════════════════════

def test_d2_operation_is_scalar_while_what_axes_are_sets():
    """operation 만 스칼라(str), domain/metric/dimensions 는 list — 다의도 표현 불가의 뿌리."""
    fields = Intent.model_fields
    assert fields["operation"].annotation is str          # HOW = 하나만
    for axis in ("domain", "metric", "dimensions"):
        assert fields[axis].annotation == list[str]        # WHAT = 여럿 OK
    # 즉 "진단 AND 비교 AND 분해"를 operation 한 칸에 못 담음 (= 붕괴1).


# ════════════════════════════════════════════════════════════════════
# D3 — artifact 키 충돌  (§2.2 B)
#   find_in_previous = first-match. 같은 키를 2 todo 가 생산하면 나중 것이 가려짐.
#   메타데이터(count)는 무해 가능 / 의미론 키(sentiment_distribution)는 유해.
#   FAIL(=후보요건) iff 의미론 키 충돌이 후속에 틀린값을 먹임.
# ════════════════════════════════════════════════════════════════════

def test_d3_metadata_count_collision_first_match_masks_later():
    """무해 가능성 명시된 *대조군* — 수집기 2개가 모두 'count' 생산 → find_in_previous 첫 것만.

    메타데이터(count)라 *유해성은 미검증* — 후속이 특정 count 를 안 쓰면 무해.
    아래 semantic 테스트(유해 후보)와의 대비용 baseline. (진단성 약함 — 의도된 대조.)
    """
    prev = {
        "t1_meta": {"meta_ads_raw": [{"x": 1}], "count": 15},
        "t2_naver": {"naver_sa_raw": [{"y": 2}], "count": 42},
    }
    # 두 count 가 있지만 하나만 회수됨 (dict 삽입순 = t1 먼저)
    assert find_in_previous(prev, "count") == 15
    # naver(42)는 'count' 이름으로는 영영 회수 불가 — 마스킹 확정.


def test_d3_semantic_key_collision_is_the_real_risk():
    """예방적 박제(현재 미발생): 같은 의미 키(sentiment_distribution) 2개면 첫 것만 회수.

    검증(wbvbfeoys) qualifier: 이 prev dict 는 fan-out 가정 하의 *가상* 재현이다.
    현 카탈로그엔 sentiment_distribution 생산자가 sentiment_analyzer 하나뿐(team_catalog
    :519) — 즉 **현 단일경로에선 이 충돌이 발생하지 않는다.** "채널별 감성" 다채널 fan-out
    이 도입되면 그때 의사결정에 직접 영향(틀린 분석 소비) → 재설계 시 *예방* 대상. 지금은 미발생.
    """
    prev = {
        "ch_meta": {"sentiment_distribution": {"positive": 0.9, "channel": "meta"}},
        "ch_naver": {"sentiment_distribution": {"positive": 0.2, "channel": "naver"}},
    }
    got = find_in_previous(prev, "sentiment_distribution")
    # naver(0.2, 부정 우세)가 있는데도 meta(0.9)만 회수 → 후속 보고서가 meta 만 봄
    assert got["channel"] == "meta"
    assert got["positive"] == 0.9
    # 해법(namespacing/versioning/merge)은 이 테스트 범위 밖 — 충돌 *발생*만 박제.


# ════════════════════════════════════════════════════════════════════
# D4 — report_writer silent-COMPLETE  (§2.2 B) ★ 검증이 내 grep 오판을 잡은 지점
#   예측이던 'orphan→SKIP'은 틀림. report_writer 는 consumes 미선언 → 게이트 무검사
#   → 빈 데이터로도 LLM 보고서 생성(silent-COMPLETE). + catalog↔code 3중 drift.
# ════════════════════════════════════════════════════════════════════

def test_d4_report_writer_declares_consumes_so_gate_catches_empty():
    """수정 반전(2026-06-07, G3): report_writer 가 consumes=[insights] 선언 → 게이트가 빈 입력 SKIP.

    원래 버그(consumes 미선언 → 게이트 사각지대)는 git history 참조.
    canonical 수정 테스트: test_silent0_fix_r1.py::test_t1_*
    """
    pool = get_agent_pool()
    meta = pool.get_tool_meta("report_text_agent", "report_writer")
    assert meta is not None
    # consumes 선언됨 (게이트가 보는 키)
    assert "insights" in (meta.get("consumes") or [])
    # 게이트 동작: 빈 previous_results 면 SKIP 사유 반환(=빈 보고서 차단)
    assert check_consume_sufficiency(meta.get("consumes") or [], {}) is not None


def test_d4_catalog_code_drift_partially_fixed():
    """G3(2026-06-07): consumes 정합 + analysis_results orphan 제거.
    D5(2026-06-08): produces drift 도 해소 — 코드 반환을 report_markdown 으로 정합.

    수정 전: params_required=[analysis_results](orphan), produces=[report_markdown], consumes 없음, 코드 report_text.
    수정 후: consumes=[insights], analysis_results 제거, 코드·catalog·다운스트림 모두 report_markdown.
    """
    pool = get_agent_pool()
    meta = pool.get_tool_meta("report_text_agent", "report_writer")
    # G3: orphan 제거 + 코드가 읽는 insights 를 consumes 로 선언
    assert "analysis_results" not in (meta.get("params_required") or [])
    assert "insights" in (meta.get("consumes") or [])
    # D5: produces == 코드 반환 키 (report_markdown) — drift 0
    assert meta.get("produces") == ["report_markdown"]


def test_d4_analysis_results_is_orphan_no_producer():
    """report_writer 가 요구하는 analysis_results 를 *생산*하는 tool 이 카탈로그에 0개.

    설령 report_writer 가 consumes:[analysis_results] 로 고쳐도 producer 부재 → 별도 배선 필요.
    """
    pool = get_agent_pool()
    all_produces: set[str] = set()
    for agent_name in pool.list_agents():
        agent = pool.get_agent(agent_name)
        for tool in agent.tools:
            all_produces.update(tool.get("produces", []) or [])
    assert "analysis_results" not in all_produces  # orphan 확정


def test_d4_fix_direction_declaring_consumes_would_let_gate_catch_empty():
    """수정 방향 박제: report_writer 가 consumes 를 선언했다면 게이트가 빈 입력을 잡는다.

    (계획서 D4 재설계 함의② = B2.1 확장. 지금은 consumes 미선언이라 못 잡을 뿐.)
    """
    # 가상으로 consumes 선언했다고 가정 → 빈 previous_results 면 SKIP 사유 반환
    reason = check_consume_sufficiency(["sentiment_distribution"], {})
    assert reason is not None
    assert reason["reason"] == "data_insufficient"
    assert reason["artifact"] == "sentiment_distribution"


# ════════════════════════════════════════════════════════════════════
# D4-chain — silent-0 end-to-end (검증 wbvbfeoys 가 지목한 11개의 최대 공백)
#   개별 고리(D4)는 박았으나 *연쇄*("빈 입력→분석 COMPLETED→degrade 미발동→환각 보고서")
#   를 한 테스트로 안 묶었음. 여기서 responder 레벨로 직접 재현 (LLM 불요, fake ExecutionResult).
# ════════════════════════════════════════════════════════════════════

def test_d4_silent0_hallucinated_analysis_defeats_honest_degrade():
    """★silent-0 연쇄 재현: 상류 0건이어도 비-collector 분석이 COMPLETED 면 정직-degrade 가 안 걸린다.

    경로: review_normalizer SKIPPED(데이터 0건) → 그러나 insight_extractor 는 consumes
    미선언(D4)이라 게이트 통과 → 빈 입력에도 COMPLETED + 환각 insights → responder 의
    `produced` 휴리스틱(responder.py:109-114)이 "collector 아닌 COMPLETED 있음 = 부분성공"
    으로 오인 → build_insufficient_data_payload 가 None → degrade 미발동 → 환각 보고서가 사용자에게.
    """
    er = ExecutionResult(todos={
        "t1": _todo("t1", "review_collector", TodoStatus.COMPLETED, {"raw_reviews": [], "count": 0}),
        "t2": _todo("t2", "review_normalizer", TodoStatus.SKIPPED, _INSUF),
        # insight_extractor: 빈 입력에도 COMPLETED + 환각 insights (게이트가 consumes 미선언이라 못 막음)
        "t3": _todo("t3", "insight_extractor", TodoStatus.COMPLETED,
                    {"insights": [{"title": "긍정 여론 우세", "description": "(빈 입력에서 LLM 이 지어냄)"}], "count": 1}),
    })
    # 상류 0건이니 정직 degrade 가 옳으나, produced=True(insight_extractor COMPLETED) 라 None.
    assert build_insufficient_data_payload(er) is None  # 버그 재현(현 동작). 수정 시 not None 으로 뒤집힘.


def test_d4_contrast_no_hallucinated_analysis_does_degrade():
    """대조군: 환각 분석(t3)을 *빼면* 같은 0건 상황에서 정직-degrade 가 정상 발동.

    유일 차이(t3 환각 COMPLETED 유무)가 silent-0 를 가름 = responder `produced` 휴리스틱이 linchpin.
    """
    er = ExecutionResult(todos={
        "t1": _todo("t1", "review_collector", TodoStatus.COMPLETED, {"raw_reviews": [], "count": 0}),
        "t2": _todo("t2", "review_normalizer", TodoStatus.SKIPPED, _INSUF),
    })
    assert build_insufficient_data_payload(er) is not None  # 환각 분석 없으면 정직 degrade 정상


# ════════════════════════════════════════════════════════════════════
# D7 — quantifier ALL 자동전개 주체 부재  (§2.2 B)
#   Intent 에 quantifier 필드 없음 → "모든 채널"을 구조적으로 못 담음.
#   (우선순위는 §1.3 코퍼스 빈도 게이트(P6)에 따름 — 여기선 *capability 부재*만 사실로.)
# ════════════════════════════════════════════════════════════════════

def test_d7_intent_has_no_quantifier_field():
    """사실: Intent 분석 4칸(operation/domain/metric/dimensions) + sub_intents(S1 씨앗) — 'ALL/모든' 양화사 자리 없음.

    검증(wbvbfeoys) qualifier: *필드 부재*는 사실이나, 이것이 실제 쿼리를 fail 시키는지·
    "모든 채널" 빈도(P6 코퍼스 게이트)는 **미검증** → 우선순위 보류. 스키마 사실로만 신뢰.
    (2026-06-09: sub_intents 다의도 씨앗 추가 — D1/D2(operation 스칼라) 구멍을 메우기 시작. D7 quantifier 구멍은 그대로.)
    """
    assert set(Intent.model_fields.keys()) == {"operation", "domain", "metric", "dimensions", "sub_intents"}
    assert "quantifier" not in Intent.model_fields  # D7 구멍 존속 — 양화사 전개 주체 여전히 없음
    # → "모든 채널"은 domain/metric 에 NL 로 남거나 LLM 자의 해석. 결정론 전개 주체 없음.


# ════════════════════════════════════════════════════════════════════
# D8 — dashboard ref 입력경로 부재  (§2.2 C / Q-B "지금 페이지")
#   cognitive 는 user_input/language/conversation_history 만 읽음 → 대시보드 상태 못 받음.
# ════════════════════════════════════════════════════════════════════

def test_d8_cognitive_prompt_ignores_dashboard_state():
    """사실: cognitive 프롬프트 입력 채널에 대시보드 상태가 없다 (user_input/language/context만).

    검증(wbvbfeoys) qualifier: 프롬프트가 dashboard_items 를 안 쓰는 건 사실이나, (a) 실
    endpoint/state 가 dashboard 를 *전혀* 못 받는지는 후속 검증, (b) "지금 페이지" 빈도(P6
    코퍼스 게이트) 미검증. "해석 불가"(영향 단정) 아님 — "입력 채널 부재"(관찰 사실)만 박제.
    """
    state = {
        "user_input": "지금 페이지의 데이터 어떻게 나온건지 분석해줘",
        "language": "ko",
        "conversation_history": [],
        "history_limit": 5,
        # 대시보드 상태를 넣어봐도(가상 키) cognitive 가 안 읽음
        "dashboard_items": [{"id": "chart_5", "metric": "roas", "value": 3.2}],
    }
    template = "INPUT={user_input}|LANG={language}|CTX={context_summary}"
    prompt = prepare_cognitive_prompt(state, template)

    assert "지금 페이지" in prompt            # 원문 NL 은 통과
    assert "chart_5" not in prompt            # 대시보드 항목 id 는 소실
    assert "3.2" not in prompt                # 대시보드 값 소실
    # → "지금 페이지"가 *무엇*인지 cognitive 가 알 길이 없음 (입력 경로 부재).
