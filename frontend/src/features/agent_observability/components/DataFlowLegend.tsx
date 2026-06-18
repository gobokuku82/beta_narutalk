/**
 * DataFlowLegend — 데이터 전달 3 메커니즘(State / Context / Class) 정적 설명.
 *
 * 사용자 요구 R12·R14 직접 답: "data 가 class/context/state 로 어떻게 전달되나".
 *  코드에 박힌 구조(검증됨, 계획서 §4.5.1)를 한눈에. Phase 1 = 정적 설명.
 *  Phase 2~3(§9-C/D)에서 todo별 *런타임* 데이터 여정(어떤 source 몇 건 → out)을 덧붙일 예정.
 */
const ITEMS: { tag: string; title: string; where: string; desc: string }[] = [
  {
    tag: 'State',
    title: 'AgentState (노드 간)',
    where: 'states/agent_state.py',
    desc: 'LangGraph TypedDict. 각 노드가 Command(update=…, goto=…)로 갱신. structured_query → plan → execution_result → response 로 흐름.',
  },
  {
    tag: 'Context',
    title: 'ExecutionContext (agent → tool)',
    where: 'models/execution.py',
    desc: 'tool.execute(params, context)의 2번째 인자. previous_results 가 이전 phase 출력을 다음 todo 로 흘려보냄(chaining). client_id·session_id 운반.',
  },
  {
    tag: 'Class',
    title: 'BaseTool.fetch → DataSource (tool ↔ 데이터)',
    where: 'tools/base_tool.py',
    desc: 'tool 은 self.fetch(source_id)로만 데이터 접근. client 는 context.client_id 에서만 흐름(ADR-022). data layer / tool layer 분리가 코드에 박힘.',
  },
];

export function DataFlowLegend() {
  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <div className="grid gap-3 sm:grid-cols-3">
        {ITEMS.map((it) => (
          <div key={it.tag} className="rounded-md border border-border/60 bg-muted/20 p-3">
            <div className="flex items-center gap-2">
              <span className="rounded-sm bg-primary/10 px-2 py-1 font-mono text-xs font-semibold text-primary">
                {it.tag}
              </span>
              <span className="text-sm font-medium">{it.title}</span>
            </div>
            <code className="mt-1 block text-2xs text-muted-foreground">{it.where}</code>
            <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{it.desc}</p>
          </div>
        ))}
      </div>
      <p className="mt-2 text-2xs text-muted-foreground/80">
        ⓘ Phase 1 = 정적 구조 설명. 런타임 데이터 여정(어떤 source를 몇 건 읽어 어떤 결과가
        다음 todo로 전달됐는지)은 백엔드 계측(Phase 2~3) 후 todo별로 표시됩니다.
      </p>
    </div>
  );
}
