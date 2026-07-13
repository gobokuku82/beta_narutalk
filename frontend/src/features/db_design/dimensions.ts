/**
 * 차원 추출 도우미 — 순수 탐지 로직.
 *
 * 팩트(실적) 테이블의 "키 칼럼"을 별도 마스터(차원) 테이블로 분리하도록 제안한다.
 * = 정규화 자동화. 실제 적용(테이블 생성 + FK 연결)은 store.applyDimensions.
 *
 * 이 페이지는 *설계/명세*만 담당하므로 raw 데이터(고유값)는 보관하지 않는다 →
 * 마스터는 "구조"(PK + 이름 칼럼 자리)만 만들고, 실제 행 적재(SELECT DISTINCT)는
 * 다운스트림(Claude Code/SQL) 몫. 탐지는 데이터가 아니라 *이름 휴리스틱* 기반
 * (auto-FK 와 동일 철학 — 추론이라 100% 아님, 사용자가 고르고 다듬는다).
 */
import type { ErdTable, ErdColumn } from './store';

export interface DimensionSource {
  tableId: string;
  tableName: string;
  columnId: string;
}

export interface DimensionSuggestion {
  /** 마스터 PK 가 될 키 이름 (예: 거래처ID) */
  key: string;
  /** 키 타입 (소스 칼럼 또는 기존 마스터 PK 타입) */
  keyType: string;
  /** 만들거나(생성) 연결할 마스터 테이블명 (예: 거래처) */
  masterName: string;
  /** 이미 같은 PK 를 가진 단일-PK 마스터가 있으면 그 이름 — 생성 대신 *연결*만 */
  existing: string | null;
  /** 이 키를 가진(연결 대상) 팩트 칼럼들 — 여러 테이블에 흩어져 있을 수 있음 */
  sources: DimensionSource[];
}

/** 비교용 정규화 — 트림 + 소문자화(한글 무영향). 복수형 's' 는 *건드리지 않음*(오병합 방지). */
const norm = (s: string): string => s.trim().toLowerCase();

/** 규칙2/마스터 매칭에서 제외할 일반명 — 테이블 단서가 없어 키로 못 씀 (store.GENERIC_PK_NAMES 와 동일 취지). */
const GENERIC_NAMES = new Set([
  'id', 'uuid', 'pk', 'key', 'no', 'seq', 'code', 'idx',
  '코드', '번호', '순번', '구분', '키',
]);

/** 키처럼 보이는 접미사 (이름만으로 키 후보로 인정). 접미사보다 긴 이름만. */
const KEY_SUFFIX = /(_?id|코드|번호|키)$/i;

/** 칼럼 이름이 "키 후보"인가 — 일반명 단독은 제외, 키 접미사를 가진 것만. */
export function isKeyLike(name: string): boolean {
  const n = name.trim();
  if (!n) return false;
  if (GENERIC_NAMES.has(n.toLowerCase())) return false;
  return KEY_SUFFIX.test(n);
}

/** 키 이름 → 마스터 테이블명 추정. 키 접미사(ID/코드/번호…)를 떼서 엔티티명만 남김. */
export function deriveMasterName(name: string): string {
  const n = name.trim();
  const stripped = n.replace(/[_\s]?(id|코드|번호|키|key|no)$/i, '').replace(/_+$/, '').trim();
  return stripped || n;
}

/**
 * 차원 추출 후보 제안. 단일-PK 마스터가 이미 있으면 *연결*(existing), 없고 키처럼 보이면 *생성*.
 * 같은 키 이름은 여러 테이블에 걸쳐 하나의 제안으로 묶고(sources[]), 일반 속성(담당자 등)은
 * 노이즈 방지를 위해 키 접미사가 없으면 제외(→ 수동 추출로 커버).
 */
export function suggestDimensions(tables: ErdTable[]): DimensionSuggestion[] {
  // 단일-PK 마스터 색인 (정규화된 PK 이름 → 후보들). 충돌(>1)이면 모호 → 연결 안 함.
  const masters = new Map<string, { table: ErdTable; pk: ErdColumn }[]>();
  for (const t of tables) {
    const pks = t.columns.filter((c) => c.pk);
    const pk = pks.length === 1 ? pks[0] : undefined;
    if (!pk) continue;
    const k = norm(pk.name);
    const list = masters.get(k) ?? [];
    list.push({ table: t, pk });
    masters.set(k, list);
  }
  const usableMaster = (k: string): { table: ErdTable; pk: ErdColumn } | null => {
    const list = masters.get(k);
    return list && list.length === 1 ? (list[0] as { table: ErdTable; pk: ErdColumn }) : null;
  };

  // 후보 칼럼을 정규화 이름으로 그룹핑.
  const groups = new Map<string, { name: string; type: string; sources: DimensionSource[] }>();
  for (const t of tables) {
    for (const c of t.columns) {
      if (c.pk || c.fk) continue;
      const k = norm(c.name);
      const hasMaster = masters.has(k); // 모호 포함 — 마스터가 있으면 비키명도 포함(연결 후보)
      if (!hasMaster && !isKeyLike(c.name)) continue; // 마스터 없고 키도 아니면 제외(노이즈 방지)
      const g = groups.get(k) ?? { name: c.name, type: c.type, sources: [] };
      g.sources.push({ tableId: t.id, tableName: t.name, columnId: c.id });
      groups.set(k, g);
    }
  }

  const out: DimensionSuggestion[] = [];
  for (const [k, g] of groups) {
    if (g.sources.length === 0) continue;
    const master = usableMaster(k);
    out.push({
      key: master ? master.pk.name : g.name,
      keyType: master ? master.pk.type : g.type,
      masterName: master ? master.table.name : deriveMasterName(g.name),
      existing: master ? master.table.name : null,
      sources: g.sources,
    });
  }
  // 생성 제안을 먼저(가치↑), 그 안에서 소스 많은 순.
  out.sort((a, b) => {
    if ((a.existing === null) !== (b.existing === null)) return a.existing === null ? -1 : 1;
    return b.sources.length - a.sources.length;
  });
  return out;
}
