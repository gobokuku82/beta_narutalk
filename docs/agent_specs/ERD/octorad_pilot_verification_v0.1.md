# octorad data_pilot 검증 리포트 v0.1

> 적대적 4렌즈(drift · 로직 · 커버리지 · 의미) 종합. deterministic 8/8·12/12 PASS가 놓친 정의·스키마·로직·커버리지·의미 불일치를 실파일 직독으로 적발.
> 생성: 2026-06-14 · 검증 대상: `backend/app/data_pilot_project/` + `data/clumi/_canonical/` 산출물 + `docs/agent_specs/ERD/octorad_canonical_contract_v0.1.yaml`
> 모든 finding은 실파일 직독 근거. 종합 작성 시 핵심 HIGH 6건을 원본 file:line 재확인(아래 §정직성 평가 검증 로그).
>
> ★ **역반영 완료 (2026-06-14, 같은 턴)**: P0 클러스터 즉시 수정 → pilot 재검증 8/8·12/12 유지.
> - **클러스터1 C6.3**(B1·D2·A4): kakao/talktalk → `msg_cost_krw`·`msg_roi_pct`(2576%·8731%) 분리. 광고 `channel_roas_x`에서 제거. contract ad_cost/conversion_revenue sources에서 제거 + msg_cost_krw 신설 + msg_roi_pct formula 정정.
> - **클러스터2**(A3·C5·D5): `order_revenue_krw` contract measures 정식 등재(source orders.payment_amount·filter C40 제외).
> - **A2** campaign_id 17→18자리 정정. **D1** config GA4 `purchase_revenue`(native KRW) 추가. **total_ad_cost→total_marketing_cost**(ad+msg) 정직 재명명.
>
> ★ **P1 역반영 완료 (2026-06-14, 같은 스트림)**: 검증 *게이트화* — 산출물이 아닌 *검증 자체*의 정직성 보강.
> - **C1·C2·C3 coverage**: `coverage.py` 신설 → contract **44필드 status 매니페스트**(materialized/tested/blocked/not_attempted) + 배지 **"13/44 materialized · 7 tested · 4 blocked · 31 not_attempted"** + not_attempted 미정당화 시 FAIL·materialized-untested WARN. 'full PASS' 착시 제거.
> - **B3 crosswalk**: `verify_outputs` 에 WARN 상태 도입 + `cross_channel_groups==0` WARN 검사(무용 가시화, '연결됨' 착시 차단).
> - **클러스터3 A1·A2 dict gate**: `dict_gate.py` 신설 → 사전↔raw 실헤더↔contract 컬럼 **자동 diff**. 실측: **CRITICAL 0**(contract source 전부 raw 실재=P0 정합 유지) · **DRIFT 18**(naver `stat_dt`/`camp_id`/`convCnt` 등 사전 오기 — ★사전 *계산내용* 수정은 오너 영역이라 *보고만*, 비차단). deterministic 값검증이 못 잡던 정의 drift 를 매 실행 가시화.
> - 통합: `gate.py`(materialize→4단 일괄, OVERALL ✅). **잔여**: 클러스터4 multi-omni/USD/비4월 mock(P2/P3)·tools 전환 = 후속(§⑤).

---

## ① 요약

**산출물은 "이 mock에 한해" 제대로 구현됐는가 — 조건부 YES.**
구현된 ~7개 필드의 산출 숫자(MER 6.53, total_ad_cost 18,306,923, blended ROAS 3.07)는 현 mock 데이터에서 산술적으로 정답이다. 그러나 "정답인 이유"는 코드가 옳아서가 아니라 **mock의 우연한 단순성**(전부 2026-04 단일월, currency 전부 KRW, advoost VT=0, Meta omni_purchase 중복 0, 영문↔한글 name 교차 0) 덕분이다. 실데이터(USD·다월·VT>0·다중 attribution)로 가면 **침묵하며 틀린다(silently wrong)**.

**deterministic 8/8·12/12 PASS는 과대포장이다.** 두 검증기는 "구현이 contract대로 raw를 처리했는가"의 일부(~6 measure / 2 metric)만 검사할 뿐, (a) contract·사전 자체가 raw와 일치하는가, (b) 만들지 않은 ~30개 필드의 부재, (c) crosswalk의 목적 달성 여부를 **구조적으로 검사하지 않는다**. 침묵이 녹색으로 렌더된다.

### Severity 집계

| Severity | 건수 | 비고 |
|---|---|---|
| **HIGH** | **11** | drift 4 · 로직 3 · 커버리지 3 · 의미 3 (일부 동일 근본원인 교차) |
| MEDIUM | 9 | drift 2 · 로직 3 · 커버리지 2 · 의미 2 |
| LOW | 8 | drift 2 · 로직 4 · 커버리지 1 · 의미 1 |

> HIGH 11건은 4렌즈가 독립 적발했으나 **근본 원인은 4개 클러스터로 수렴**한다(§③ 참조): **[C6.3 메시징/광고 혼입]**(로직·의미·drift 3렌즈 동시 적발) · **[order_revenue_krw SPEC 공백]**(3렌즈) · **[사전↔raw drift]**(ccnt 역전·campaign_id 자릿수) · **[검증 커버리지 공백]**(crosswalk 0% + 35필드 미검사).

---

## ② 렌즈별 finding 표

### 렌즈 A — drift (사전↔raw↔contract 정의/스키마/인코딩)

| # | issue | severity | evidence | recommendation |
|---|---|---|---|---|
| A1 | 사전 `ccnt` 의미·타입이 raw와 역전 (statDt보다 위험) | **high** | 사전 `clumi_data_dictionary.csv:52` `ccnt,decimal,CVR (%),2.63` + `:49 convCnt,integer,전환 수`. 그러나 contract:78 `ccnt 전환수(int) — convCnt 부재(06 검증)`, cleaned/kakao 등 구현은 ccnt=전환수로 처리. 즉 **사전만 틀림**(ccnt를 CVR%로, 존재하지 않는 convCnt를 전환수로 오기) | 사전 naver_searchad 행 재작성: convCnt 삭제, ccnt→int/전환수. 사전→contract 자동 diff 게이트 추가(값 검증만으론 못 잡음) |
| A2 | meta campaign_id 자릿수 사전·contract 모두 17자리라 했으나 raw·산출물은 18자리 | **high** | contract:172 `meta: data[].campaign_id(17자리)`. 그러나 crosswalk 산출물 멤버 ID = `120210000000012346` 등 **18자리**(line 41 등). 사전·contract 동시 오기 | contract:172 `(17자리)`→`(18자리)` 정정. crosswalk 매칭이 자릿수에 의존하지 않는지 확인 |
| A3 | orders cleaned `order_revenue_krw` measure가 contract에 전혀 미정의 (SPEC 공백) | **high** | cleaned/orders_2026-04.json:3 `order_revenue_krw: 119539660` 생성. contract grep `order_revenue`/`payment_amount` 모두 **0건**. orders는 contract에서 dimension source로만 등장 | contract measures에 order_revenue_krw 정식 추가(source orders.payment_amount, transform cast_int, 단위/필터 명시) 또는 commerce contract로 분리 |
| A4 | contract 자기모순: kakao/talktalk 메시징 cost가 ad_cost_krw로 매핑 + msg_roi_pct가 미정의 `msg_cost` 참조 | **high** | contract:38-39 ad_cost_krw sources에 kakao/talktalk `summary.total_cost_krw` 포함. :160 msg_roi_pct formula `(... / msg_cost - 1)*100`의 `msg_cost`는 measures에 **정의 없음**. 유일 메시징 cost는 ad_cost_krw에 바인딩 | msg_cost measure 신설, kakao/talktalk total_cost_krw를 msg_cost에 바인딩. ad_cost_krw sources에서 kakao/talktalk 제거(MER 분모 오염·C6.3 위배 해소) |
| A5 | raw CSV 18개 전부 UTF-8 BOM — contract/config는 bare 컬럼명 참조 | medium | raw `*.csv` 첫 3바이트 `EF BB BF`(`﻿report_date`로 파싱). config advoost는 `report_date`·`cost` bare 참조. 8/8 산출물이 채워진 걸 보면 구현은 utf-8-sig지만 SPEC·config 어디에도 미명시 | config meta에 `encoding=utf-8-sig` 규약 명시 또는 raw 생성 시 BOM 제거. '첫 컬럼명==기대명' assert 추가 |
| A6 | orders/customers 사전 스키마가 raw와 다수 불일치 | medium | 사전 orders에 guest_email_hash·region·customer_gender 명시하나 raw 헤더에 부재; raw의 referrer·created_at·used_point는 사전에 없음. 사전 customers `membership_grade`/`membership_point` vs raw `member_grade`/`available_point`(contract:190은 member_grade로 올바름) | 사전 orders/customers 컬럼을 raw 헤더 기준 재생성. 매핑코드가 가정한 컬럼 제거 |
| A7 | 사전이 raw·contract가 쓰는 컬럼 누락 (event_time_unix, kakao open_count/total_cost 등) | low | raw ad_change_history `event_time_unix` 존재 + contract:209 참조하나 사전 누락. kakao summary open_count/click_count/total_cost_krw 존재 + contract:38,120,121 참조하나 사전 미기재 | 사전을 contract sources[]가 참조하는 raw 필드와 cross-check 보강, 또는 raw 실헤더 자동 생성 전환 |
| A8 | naver_interest_alert raw에 존재하지 않는 달력 날짜 (2026-02-30 등) | low | raw `snapshot_datetime=2026-02-30 23:59:59`(2월 30일 부재) + `2026-03-30`(월말 아님). month-end 가정 코드 시 예외/오정렬 가능 | raw 생성 시 calendar-aware 월말로 정정(2026-02-28, 2026-03-31) |

### 렌즈 B — 로직/엣지 버그 (pilot 코드)

| # | issue | severity | evidence | recommendation |
|---|---|---|---|---|
| B1 | C6.3 위반: 메시징 전환매출이 광고 blended_platform_roas 분자에 혼입 | **high** | `compute.py:8` AD_CHANNELS에 kakao/talktalk 포함. :14 total_ad_cost·:24 total_platform_rev가 메시징비/매출을 광고와 합산. blended 분자에 메시징 전환매출, MER 분모에 kakao 59,020+talktalk 12,450이 광고비로 들어감. verify는 channel별 cost 일치만 봄 | 메시징은 msg_ measure로 분리, compute의 AD_CHANNELS/blended 분자에서 제외. MER 분모 메시징비 포함 여부 명시 결정 |
| B2 | meta 추출은 first-match인데 검증은 sum — 다중 attribution window 시 발산 | **high** | `transforms.py:82-85` meta_action_extract는 첫 항목만 `return`. verify_outputs는 omni_purchase 전부 합산. mock은 >1 omni row=0이라 EQUAL→PASS. 실 Meta는 attribution window별 복수 출현→pipeline 과소계상, 자기참조로 검증이 못 잡음 | meta_action_extract를 sum 기반으로(통상 합산이 맞음), verify와 동일 로직 공유. 다중 omni row mock 추가 |
| B3 | crosswalk가 stated 목적(cross-channel 연결) 0% 달성하나 '성공'으로 materialize·검증 대상 아님 | **high** | crosswalk.json: canonical_groups=22, **cross_channel_groups=0**, unlinked=3. 25 campaign 중 채널 간 묶음 0. 원인: meta 영문코드 vs advoost/internal/kakao 한글을 _norm_name(lower+공백제거)로는 절대 같은 키 안 됨. naver_sa는 campaign_name raw 부재로 전부 unlinked. verify_outputs에 crosswalk 검사 0건 | cross_channel_groups==0이면 verify에서 WARN/FAIL. UTM/campaign code 매핑 사전 또는 internal master 허브 전략 재설계. '연결됨'처럼 materialize 금지 |
| B4 | advoost vt_conversion_count(SPEC A4) 미구현 — VT>0 시 전환 침묵 누락 | medium | contract:81-87 vt_conversion_count 정식 정의. pipeline은 click_through_conversions(CT)만 매핑, view_through 미출력. mock VT=0이라 손실 0→통과. VT>0 실데이터면 silent drop | m_advoost에 vt_conversion_count 추가, CT와 별도 유지. VT>0 mock 회귀 |
| B5 | period 필터가 이 mock에서 사실상 no-op·미실행 + kakao/talktalk는 period=None | medium | meta/naver/advoost 전부 2026-04이라 필터가 한 행도 제외 안 함(분기 미실행). kakao/talktalk는 period=None이라 월 필터 부재 — 우연히 전부 4월. 비4월 row 추가 시 무조건 합산→기간 오염 | kakao/talktalk도 기간 필터 적용 또는 'raw 단일기간' 불변식 assert. 비4월 mock으로 분기 실행 테스트 |
| B6 | lineage(신뢰/감사) 샘플이 0값 row를 잡아 무의미한 provenance | medium | lineage는 'val is not None'인 첫 row 채택, 0도 not None. naver_sa lineage conversion_revenue value=0(source=0) — 0→0 매핑은 변환 검증 가치 0 | 샘플 선택을 'val not in (None,0)' 또는 대표 비영 row로 |
| B7 | pct_to_ratio 더블 라운딩 + cast_int 절사 — 체계적 편향 | low | `transforms.py:31-34` cast_float2(round2) 후 /100 후 round4(이중 반올림). cast_int=int(float(v)) 절사. currency convert는 cast_int 먼저→소수부 버린 뒤 환율 곱(USD 손실). mock은 정수·KRW라 손실 0 | pct_to_ratio는 float(v)/100 한 번만 round. currency는 환율 곱 후 마지막에 round |
| B8 | verify 교차검증이 전월(3월) GA4 purchase를 4월 한정 orders와 비교 | low | verify는 ga4 purchase를 period 필터 없이 카운트(3월+4월 혼재)→4월 orders와 비교. 분자만 다월·substring 매칭이라 비대칭 | GA4 purchase도 event_date 4월 필터 후 비교, substring 대신 json 파싱 |
| B9 | PERIOD 상수 6중 하드코딩 + 실제 필터 미사용(라벨 전용) | low | PERIOD='2026-04'는 schema 라벨만. 실 필터는 각 채널 tuple·파일명에 '2026-04' 별도 6회 하드코딩. 기간 변경 시 라벨/데이터 드리프트 | PERIOD 단일 상수를 모든 필터·파일명에 참조시켜 SSOT화 |

### 렌즈 C — coverage/honesty (contract 42필드 vs 산출물)

| # | issue | severity | evidence | recommendation |
|---|---|---|---|---|
| C1 | 42필드 중 ~7개만 materialize인데 full PASS로 제시, 검증기가 부재를 못 잡음 | **high** | contract=42필드(14 measure+11 metric+15 dim+2 time). 산출 union=ad_cost_krw·clicks·conversion_count·conversion_revenue_krw·impressions(5/14)+order_revenue_krw. computed=roas_x·mer(2/11). verify 12개 chk가 전부 동일 ~6 measure/2 metric 대상. link_clicks·msg_*·ctr/cvr·모든 dimension·time field 미검사→8/8·12/12가 미구현 다수 위에서 vacuously green | _schema/coverage.json에 42필드 status(materialized/blocked/not_attempted) 매니페스트 + not_attempted 미정당화 시 FAIL. 배지를 'N/42 materialized, M tested'로 재표기 |
| C2 | non-blocked 메시징 measure 다수 silent drop, blocked 4건만 정직 선언이라 메시징 처리된 듯한 착시 | **high** | contract blocked=[msg_delivered/open_rate/click_rate/ctor]뿐. 그러나 non-blocked msg_target(M1)·open(M4)·click(M6)·conversion(M9)·conversion_revenue(M10)·roi(M11)·aov(M12) 정의. raw kakao summary에 open_count=1059·click_count=191·conversion_count=24·roi_percent 등 전부 존재. pipeline은 ad_cost/conversion_revenue/conversion_count만 추출, 나머지 msg 필드 마커 없이 drop. interest_alert·crm_send_logs 채널 미연결 | non-blocked msg_* materialize(데이터 이미 summary에 있음) 또는 not_attempted 매니페스트 등재 |
| C3 | dimension 15개 중 실컬럼 0개 materialize, metric 그룹화 불가 | **high** | _canonical에 dimension 컬럼 없음. crosswalk가 유일 dim artifact인데 cross_channel=0. 모든 measure는 channel×month 단일 스칼라 SUM(meta rows=90 collapse). report_date·event_ts per-row 미출력. member_id·rfm_tier·utm_*·device 등 11 dim 부재(customers/orders/ga4 raw엔 존재) | 'aggregate-only slice(channel×month totals)'임을 명시. dimensional 범위면 report_date+campaign_id grain 최소 출력, 아니면 15 dim+2 time을 not_attempted 표기 |
| C4 | 즉시계산 가능한 metric(ctr/cvr/cpc/cpm/tacos) 부재 — 데이터 아닌 순수 coverage 공백 | medium | compute.py는 total_ad_cost·channel_roas_x·blended·order_revenue·mer만. cpc/cpm/ctr/cvr/tacos는 이미 materialize된 measure로 계산 가능, blocked도 아님. link_clicks는 raw `inline_link_clicks` 존재하나 미추출, advoost view_through_conversions도 미사용 | input 완비 6 metric을 compute.py에 추가 또는 not_attempted 등재. m_meta에서 link_clicks/reach/frequency 추출 |
| C5 | headline MER·channel ROAS가 contract 미정의 revenue source 사용 + blended가 contract 금지 cross-channel 합 | medium | contract mer.formula='total_revenue/total_ad_cost', conversion_revenue source에 orders 없음, order_revenue_krw measure 없음. compute.py는 mer=orders.payment_amount/total_ad_cost=6.53로 미선언 필드를 분자로. blended_platform_roas=3.07은 conversion_revenue(comparability:warn 'cross-channel 합산금지')의 합인데 flag 없이 peer metric으로 제시 | MER 분자=orders GMV가 contract total_revenue로부터의 의도적 deviation임을 문서화, order_revenue_krw를 contract 추가. blended에 comparability warn 부착 또는 drop |
| C6 | (balance) grain 더블카운트 가드 + statDt 날짜포맷 정정은 올바르고 정직 라벨 | low | meta_ads_performance/by_age/instagram_inapp 동일 3 campaign_id 공유, by_age spend==performance, instagram_inapp은 placement subset이라 performance-only 추출이 더블카운트 방지 정답·verify #2가 테스트. statDt=ISO(2026-04-01)로 경험적 정정+PILOT note 정직 기록 | 이 정직성을 모델로 삼아 silently-skipped ~30 필드에도 동일 규율 적용 |

### 렌즈 D — cross-source 의미 정합 (canonical 매핑 + 독립소스 교차검증)

| # | issue | severity | evidence | recommendation |
|---|---|---|---|---|
| D1 | GA4 매출이 lossy USD 필드 경유 — 동일 raw 레코드에 정확한 native KRW 필드가 존재하는데도 | **high** | raw ga4 purchase: `{purchase_revenue_in_usd:44.21, purchase_revenue:59680}`, 해당 order payment_amount=59680(KRW 정확일치). config:52는 `purchase_revenue_in_usd: currency_to_krw`(×1350) 매핑. event_params.currency='KRW'인데 값은 USD 크기(order/value=1350 전건). usd경로 114,043,248 vs native 114,043,270(mock 클린 ×1350이라 22 차이, 실 2자리 USD 반올림은 order당 ~675 손실) | ga4 매출을 ecommerce.purchase_revenue(native KRW, identity)에서 매핑. 오라벨 currency='KRW'를 known raw quirk로 문서화 |
| D2 | kakao/talktalk conversion_amount_krw가 ad측(A5)·msg측(M10) 두 measure에 동시 매핑 — C6.3 자기위반 | **high** | contract:99-100이 summary.conversion_amount_krw를 conversion_revenue_krw(A5)에, :123이 동일 필드를 msg_conversion_revenue_krw(M10)에 등재. cleaned/kakao conversion_revenue_krw=1,579,710이 ad total에 접힘→computed에서 kakao(26.77x)·talktalk(88.31x)가 channel_roas_x·blended에 포함. :122는 '광고 전환과 절대 분리(C6.3)' | conversion_amount_krw의 집을 하나로. 메시징이면 msg측 전용 라우팅+ad/blended 제외(88x/27x는 omni_purchase ad ROAS와 비교 불가). raw (table,col)→2 measure 금지 deterministic 체크 |
| D3 | cross-source 매출 reconciliation 부재 — 3개 독립소스가 2~3x 불일치, comparability flag 없음 | **high** | 4월 매출 3소스: orders 119,539,660(non-cancel) / GA4 native 114,043,270 / ad-platform conversion_revenue 합 56,236,345. platform/orders=0.453. 동일채널 교차도 발산(meta platform 17.6M vs orders meta 20.4M). contract comparability는 measure 내부만, orders·GA4·ad를 같은 경제사건으로 잇는 flag 없음 | reconciliation note 추가: orders=fact / GA4=tracking subset / ad conversion=platform-attributed(채널간 중복, 비가산). conversion_revenue를 order_revenue와 non-summable로 표시, MER은 order_revenue(이미 그러함), blended는 lower-trust 라벨 |
| D4 | Meta action_values에 omni_purchase·offsite_conversion.fb_pixel_purchase 동일값 중복 — 순진 합산 시 2x | medium | raw action_value types={offsite...:75, omni_purchase:75}, 75행 전부 동일값. naive 전체합 35,206,128 = omni-only 17,603,064의 정확히 2.0x. contract는 silent-0(미필터)만 문서화, double-purchase-type 충돌은 미문서화 | contract에 중복 타입 명시 + omni_purchase만 추출. 추출매출≠naive-allsum assert로 회귀 차단 |
| D5 | orders 매출이 미문서 필드선택(payment_amount)·미문서 status 필터(C40 제외) 적용, measure 자체 contract 부재 | medium | cleaned/orders order_revenue_krw=119,539,660/1919행. raw 4월=2000행/124,220,670. 119.5M=N00+N40, 1919=2000−81(C40 cancel 제외). payment vs product도 ~20% gap. contract에 order_revenue_krw·orders source 정의 0 | contract에 order_revenue_krw 추가: source=orders.payment_amount, transform=cast_int, 필터=C40 제외 명시(N40 포함 여부 명확화) |
| D6 | vt_conversion_count source 전부 0 + advoost CT-only vs Meta omni의 attribution universe 차이 미flag | low | raw advoost view_through=0(전90행), click_through=335. advoost roas_x 6.5가 blended 3.07에 Meta omni 기반과 섞임. CT-only(GFA) vs omni_purchase(view+click)는 동일 attribution base 아님 | vt_conversion_count 유지(비영=회귀신호). A4/A5 comparability에 advoost-vs-Meta 혼합 warn 명시 |

---

## ③ ★확정 이슈 (high/med — 고쳐야 할 것)

> HIGH 11건은 4개 근본 클러스터로 수렴. 같은 결함을 여러 렌즈가 독립 확증할수록 신뢰도가 높다.

### 클러스터 1 — C6.3 메시징/광고 혼입 (★3렌즈 동시 적발: B1·D2·A4)
contract 자체가 동일 필드 `summary.conversion_amount_krw`를 ad측 A5와 msg측 M10에 **이중 매핑**(contract:99-100 + :123)하고, `summary.total_cost_krw`를 ad_cost_krw에 바인딩(:38-39)하며, `compute.py:8`이 kakao/talktalk를 AD_CHANNELS에 넣어 **메시징비가 MER 분모를, 메시징 전환매출이 blended ROAS 분자를 오염**한다. contract:122의 '광고 전환과 절대 분리(C6.3)' 원칙과 정면 충돌. 추가로 msg_roi_pct는 정의되지 않은 `msg_cost`(contract:160)를 참조 — 메시징 ROI 산식이 dangling symbol.
**고침:** msg_cost measure 신설 → kakao/talktalk total_cost_krw를 ad_cost_krw가 아닌 msg_cost로 라우팅. conversion_amount_krw는 msg측 전용. compute의 AD_CHANNELS/blended에서 kakao/talktalk 제외.

### 클러스터 2 — order_revenue_krw SPEC 공백 (★3렌즈: A3·C5·D5)
산출물 핵심(MER 6.53 분자, total_order_revenue 119,539,660)이 **contract에 존재하지 않는 measure**다. grep `order_revenue`/`payment_amount` = 0건. 게다가 미문서 필드선택(payment vs product)·미문서 status 필터(C40 cancel 제외, 1919=2000−81)가 적용됨. deterministic sum 체크는 통과하나 lineage·단위·필터 규약이 contract 권위 밖.
**고침:** contract measures에 order_revenue_krw 정식 등재(source=orders.payment_amount, transform=cast_int, filter=C40 제외, N40 처리 명시). MER 분자가 channel revenue가 아닌 비즈니스 GMV라는 deviation을 문서화.

### 클러스터 3 — 사전↔raw drift (A1·A2; deterministic이 절대 못 잡는 종류)
값 합계 검증은 '구현이 contract대로'만 보므로 **사전·contract 자체의 오기**를 못 잡는다. (a) 사전 ccnt=CVR%·convCnt=전환수(`:49,:52`)는 raw/contract와 **정반대 역전** — statDt 오기보다 위험(전환수↔CVR% 혼동). (b) campaign_id가 사전·contract 모두 17자리(contract:172)라 단정하나 raw·산출물은 **18자리**(crosswalk member `120210000000012346`).
**고침:** 사전을 raw 실헤더 기준 재생성(수기 사전 폐기 권장). contract:172 자릿수 정정. **사전→contract 자동 diff 게이트**를 deterministic 체크에 추가.

### 클러스터 4 — 검증 커버리지 공백 (C1·C2·C3·B3·B2)
8/8·12/12는 ~6 measure/2 metric만 검사 → 42필드 중 ~35 미구현·crosswalk 0%·다중-attribution 분기가 **vacuously green**. 특히 crosswalk는 stated 목적(cross-channel 연결)을 **0% 달성**(cross_channel_groups=0)했는데 verify에 검사 0건. meta first-match vs verify sum의 자기참조(B2)도 mock 단순성에 가려짐.
**고침:** coverage.json 매니페스트(42필드 status) + not_attempted FAIL. crosswalk cross_channel_groups==0 시 WARN/FAIL. meta 추출을 sum으로 통일하고 verify와 로직 공유.

### 추가 MEDIUM 확정 (단독 근본원인)
- **D1 GA4 lossy USD 경로** — 동일 레코드에 native KRW(`purchase_revenue`)가 있는데 USD×1350 경유. native 필드로 전환.
- **D3 매출 3소스 2~3x 불일치 reconciliation 부재** — orders 119.5M/GA4 114M/ad 56.2M을 non-summable로 명시.
- **D4 Meta double-purchase-type 2x** — omni_purchase만 추출(현 구현 OK), 회귀 방지 assert 추가.
- **A5 BOM 18 CSV** — config에 encoding=utf-8-sig 규약 명시.
- **B4/C4 vt_conversion_count·6 metric 미구현** — input 완비, 추가 또는 not_attempted 표기.
- **B5/B6 period no-op·lineage 0값 샘플** — 비4월 mock 분기 테스트, 비영 row 샘플.

---

## ④ 정직성 평가 — "검증 통과가 과대포장 아닌가?"

**결론: 과대포장 맞다(honesty-overstated). 단, 구현된 슬라이스 내부는 유능하고 정직하다.**

| 항목 | 판정 | 근거 |
|---|---|---|
| 8/8·12/12 PASS가 "산출물 정확"을 보증하나? | **NO — vacuously green** | 12개 chk가 전부 ~6 measure/2 metric 대상(C1). 42필드 중 ~35 미구현은 검사 항목에 아예 없어 구조적으로 fail 불가 |
| PASS가 "contract·사전이 raw와 일치"를 보증하나? | **NO** | 값 합계 검증은 '구현이 contract대로'만 증명. ccnt 역전(A1)·campaign_id 자릿수(A2)·order_revenue SPEC 공백(A3) 등 사전/contract 오기를 못 잡음 |
| crosswalk 목적 달성을 반영하나? | **NO** | cross_channel_groups=0(목적 0% 달성)인데 verify에 crosswalk 검사 0건(B3). '연결됨'처럼 materialize |
| 산출 숫자(MER 6.53 등) 자체는 틀렸나? | **이 mock에선 정답** | salesAmt=cost/convAmt=revenue 매핑은 raw 산술로 0 mismatch 확증(naver 전건 cpc×clkCnt=salesAmt). MER 분모/분자도 이 mock 값 정확 |
| 그 정답은 코드가 옳아서인가? | **NO — mock 우연** | 단일월·전부 KRW·VT=0·omni 중복0·name 교차0 덕분. 실데이터(USD·다월·VT>0·다중 attribution)면 침묵하며 틀림(D1·B2·B4·B5) |
| 정직하게 선언된 부분은? | **일부만** | blocked 4건·statDt 정정·grain 더블카운트 가드는 정직 라벨(C6). 그러나 non-blocked msg_* 7필드·15 dim·2 time·ctr/cvr 등 ~30필드는 **'not materialized' 마커 없이** silent drop(C2·C3·C4) |
| 정직성 모범 사례 존재? | **YES** | meta grain 가드(by_age==performance, instagram=subset → performance-only 추출)와 statDt ISO 정정은 실제 작업+정직 기록. 이 규율을 silent-skip 필드에도 적용해야 |

**한 줄 정직성 판정:** 박힌 슬라이스는 competent + 정직하나, **contract-complete처럼 패키징**됐다. reference implementation으로 취급하기 전 "N/42 materialized, M tested" 정직 framing이 선행돼야 한다.

---

## ⑤ 다음 액션 (우선순위)

| P | 액션 | 근거 finding | 효과 |
|---|---|---|---|
| **P0** | **msg_cost measure 신설 + kakao/talktalk를 ad_cost_krw·AD_CHANNELS·conversion_revenue에서 제외** → C6.3 분리 복원 | B1·D2·A4 | MER 분모·blended ROAS 분자 오염 제거, contract 자기모순 해소 |
| **P0** | **order_revenue_krw를 contract measures에 정식 등재**(source/transform/C40 필터 명시) | A3·C5·D5 | headline MER 분자가 SPEC 권위 밖인 상태 해소 |
| **P0** | **사전 raw 실헤더 자동 생성 전환** + ccnt/campaign_id 정정 + **사전→contract 자동 diff 게이트** | A1·A2·A6·A7 | deterministic이 못 잡는 정의 drift를 게이트로 차단 |
| **P1** | **coverage.json 매니페스트**(42필드 status) + not_attempted FAIL + 배지 'N/42 materialized, M tested' 재표기 | C1·C2·C3 | silent gap을 가시화, full PASS 착시 제거 |
| **P1** | **crosswalk cross_channel_groups==0 시 WARN/FAIL** + UTM/code 매핑 사전 또는 internal master 허브 재설계 | B3 | crosswalk 무용을 검증에 반영, 목적 달성 경로 마련 |
| **P1** | **meta_action_extract를 sum으로 통일** + verify와 로직 공유 + 다중 omni mock row | B2·D4 | first-match vs sum 자기참조 발산 제거 |
| **P2** | **GA4 매출을 native purchase_revenue(KRW)로 전환** + currency='KRW' 오라벨 문서화 | D1 | USD round-trip 손실 제거 |
| **P2** | **매출 3소스 reconciliation note**(orders=fact/GA4=subset/ad=attributed, non-summable) + blended lower-trust 라벨 | D3·D6 | cross-source 비교가능성 계약 보강 |
| **P2** | **vt_conversion_count·ctr/cvr/cpc/cpm/tacos·link_clicks 추가** 또는 not_attempted 등재 | B4·C4 | input 완비 필드 coverage 확장 |
| **P3** | **비4월·USD·VT>0·다중omni mock row 추가** → period/currency/VT/double 분기 실제 자극하는 회귀 | B5·B2·B4·B7 | "녹색"이 실데이터 분기를 검증하도록 |
| **P3** | config에 **encoding=utf-8-sig** 규약 + '첫 컬럼명==기대명' assert | A5 | BOM 잠복 회귀 차단 |
| **P3** | pct_to_ratio 단일 round + currency 환율 후 round + lineage 비영 샘플 | B7·B6 | 정밀도 편향·무의미 provenance 정정 |

---

### 검증 로그 (종합 작성 시 원본 file:line 재확인)
- `compute.py:8,14,24,28` AD_CHANNELS에 kakao/talktalk 포함·MER 분자=orders order_revenue_krw — **확인✓**
- `transforms.py:31-34`(pct_to_ratio 이중 라운딩), `:82-85`(meta_action_extract first-match `for...return`) — **확인✓**
- contract `:38-39`(ad_cost kakao/talktalk), `:78`(ccnt 전환수), `:99-100`+`:123`(conversion_amount_krw 이중매핑), `:160`(msg_cost 미정의), `:172`(campaign_id 17자리), `:81-87`(vt_conversion_count) — **확인✓**
- contract grep `order_revenue`/`payment_amount` = **0건 확인✓**, `msg_cost`는 formula 1곳만 — **확인✓**
- 산출물 `cleaned/kakao_2026-04.json`(conversion_revenue 1,579,710), `cleaned/orders_2026-04.json`(order_revenue_krw 119,539,660/1919행), `computed/ad_metrics_2026-04.json`(mer 6.53, blended 3.07, kakao 26.77x·talktalk 88.31x), `crosswalk/campaign_crosswalk.json`(cross_channel_groups=0, unlinked=3) — **확인✓**
- 사전 `clumi_data_dictionary.csv:49,52`(convCnt 전환수 / ccnt CVR%) — **확인✓** (※ 일부 finding이 raw key로 인용한 `crto`/`cvr`은 raw naver_searchad.json 키 기준 — 사전 파일 자체엔 ror/ccnt만 존재. 사전 역전 사실은 file 직독 확정, raw-key 세부는 렌즈 seed 근거)
