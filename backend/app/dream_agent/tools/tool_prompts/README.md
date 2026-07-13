# tools/tool_prompts/ — LLM 호출 tool 의 프롬프트

**LLM 을 호출하는 tool 만** 여기에 프롬프트 YAML 을 둔다. 순수 로직 tool 은 불필요.

## 규약

- 파일명 = tool 이름: `tool_prompts/<tool_name>.yaml` → `load_tool_prompt("<tool_name>")` 로 로드
  (`tools/shared/prompt_loader.py`, lru 캐시)
- 통상 구조:

```yaml
system_prompt: |
  (역할·규칙·출력 형식)
user_template: |
  (입력 슬롯 — {placeholder} 치환은 tool 의 run_llm 이 수행)
```

## 왜 카탈로그(tools/catalog/)와 분리하는가

- 카탈로그 YAML = **계약** (produces/consumes/params) — planner·registry 가 읽고 planning 프롬프트에 주입됨
- 프롬프트 YAML = **콘텐츠** — 자주 튜닝되고, planner 가 볼 필요 없음
- 섞으면 planning 주입 컨텍스트가 비대해지고 관객(플래너 vs LLM)이 섞임

agent-stage 프롬프트는 `llm_manager/prompts/` (orchestration 자산), tool 프롬프트는 여기 (tool 소유) — 대칭 구조.
