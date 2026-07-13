/**
 * DB설계 store — ERD 스키마 모델 (Zustand).
 *
 * 시스템 → DB설계 페이지의 단일 진실 소스. 테이블/컬럼/관계(FK)를 보유하고
 * 캔버스(노드=테이블, 엣지=FK)·편집 패널·DDL 생성기가 공유한다.
 * 영속: api/hooks/useDbDesign (백엔드 GET/PUT). 출력: ddl.ts (PostgreSQL DDL).
 */
import { create } from 'zustand';
import { deriveMasterName, type DimensionSuggestion } from './dimensions';

export const COLUMN_TYPES = [
  'TEXT', 'VARCHAR(255)', 'INTEGER', 'BIGINT', 'NUMERIC', 'FLOAT',
  'BOOLEAN', 'DATE', 'TIMESTAMPTZ', 'UUID', 'JSONB',
] as const;
export type ColumnType = (typeof COLUMN_TYPES)[number];

export interface ErdFk {
  table: string; // 참조 테이블명
  column: string; // 참조 컬럼명
}

export interface ErdColumn {
  id: string;
  name: string;
  type: string; // COLUMN_TYPES 중 하나 (자유 입력도 허용)
  pk: boolean;
  nullable: boolean;
  unique: boolean;
  default?: string | null;
  fk?: ErdFk | null;
}

export interface ErdTable {
  id: string;
  name: string;
  comment?: string;
  columns: ErdColumn[];
  position: { x: number; y: number };
}

export interface ErdDesign {
  name: string;
  tables: ErdTable[];
  updated_at?: string | null;
}

/** 외부 가져오기(엑셀 등)로 들어오는 테이블 정의 — id/위치 없이 컬럼만. */
export interface ImportColumnInput {
  name: string;
  type: string;
  pk?: boolean;
  nullable?: boolean;
  unique?: boolean;
  default?: string | null;
}
export interface ImportTableInput {
  name: string;
  comment?: string;
  columns: ImportColumnInput[];
}

const uid = (): string =>
  (globalThis.crypto?.randomUUID?.() ?? `id_${Math.random().toString(36).slice(2)}`);

function newColumn(partial: Partial<ErdColumn> = {}): ErdColumn {
  return {
    id: uid(),
    name: partial.name ?? 'column',
    type: partial.type ?? 'TEXT',
    pk: partial.pk ?? false,
    nullable: partial.nullable ?? true,
    unique: partial.unique ?? false,
    default: partial.default ?? null,
    fk: partial.fk ?? null,
  };
}

function newTable(name: string, x: number, y: number): ErdTable {
  return {
    id: uid(),
    name,
    columns: [newColumn({ name: 'id', type: 'UUID', pk: true, nullable: false })],
    position: { x, y },
  };
}

/** 격자 슬롯 위치 (addTable 과 동일 규칙). */
function gridPosition(index: number): { x: number; y: number } {
  return { x: 80 + (index % 4) * 260, y: 80 + Math.floor(index / 4) * 220 };
}

/** 비교용 정규화 — 소문자화 + 단순 복수형(s) 제거. (customer ↔ customers 매칭) */
function normalizeRef(name: string): string {
  return name.trim().toLowerCase().replace(/s$/, '');
}

/** 규칙2(이름 일치)에서 제외할 일반 PK 이름 — 테이블 단서가 없어 오연결 위험이 큼. */
const GENERIC_PK_NAMES = new Set([
  'id', 'uuid', 'pk', 'key', 'no', 'seq', 'code', 'idx',
  '코드', '번호', '순번', '구분', '키',
]);

/** FK 연결 1건 — 참조 PK 의 타입을 따르고 nullable 로. */
function linkTo(c: ErdColumn, hit: { table: ErdTable; pk: ErdColumn }): ErdColumn {
  return {
    ...c,
    type: hit.pk.type,
    nullable: true,
    fk: { table: hit.table.name, column: hit.pk.name },
  };
}

/**
 * 이름 매칭 자동 FK — targets(이번에 추가된 테이블)의 컬럼만 대상(기존 설계 보존). 두 규칙:
 *  규칙1: `<참조>_id`(또는 `<참조>_<pk명>`) → 같은 이름 테이블의 PK.
 *  규칙2: 컬럼명이 다른 테이블의 PK 이름과 정확히 일치 (사번·거래처ID 등 한글 키 지원).
 * 후보는 PK 가 정확히 1개인 테이블만(복합 PK 제외). 규칙2는 일반명(id 등) 제외 + 후보 1개일 때만.
 * 추론이라 100%는 아님 — 캔버스에서 직접 수정 가능.
 */
export function linkForeignKeys(tables: ErdTable[], targets: ErdTable[]): ErdTable[] {
  const targetIds = new Set(targets.map((t) => t.id));

  // 후보 = PK 가 정확히 1개인 테이블만.
  const refs = tables
    .map((t) => {
      const pks = t.columns.filter((c) => c.pk);
      return pks.length === 1 ? { table: t, pk: pks[0] as ErdColumn } : null;
    })
    .filter((x): x is { table: ErdTable; pk: ErdColumn } => x !== null);

  // PK 이름 → 그 이름을 PK 로 갖는 후보들 (정확히 1개일 때만 규칙2 연결).
  const byPkName = new Map<string, { table: ErdTable; pk: ErdColumn }[]>();
  for (const r of refs) {
    const k = r.pk.name.trim().toLowerCase();
    const list = byPkName.get(k) ?? [];
    list.push(r);
    byPkName.set(k, list);
  }

  return tables.map((t) => {
    if (!targetIds.has(t.id)) return t;
    const columns = t.columns.map((c) => {
      if (c.pk || c.fk) return c;

      // 규칙1: <참조>_<id|pk명> — 후보 1개일 때만(동명 정규화 충돌 시 비결정 연결 방지).
      const m = c.name.match(/^(.*)_([A-Za-z0-9]+)$/);
      if (m) {
        const prefix = normalizeRef(m[1] ?? '');
        const key = (m[2] ?? '').toLowerCase();
        if (prefix) {
          const hits = refs.filter(
            (r) =>
              r.table.id !== t.id &&
              normalizeRef(r.table.name) === prefix &&
              (key === 'id' || r.pk.name.toLowerCase() === key),
          );
          if (hits.length === 1) return linkTo(c, hits[0] as { table: ErdTable; pk: ErdColumn });
        }
      }

      // 규칙2: 컬럼명 == 다른 테이블 PK 이름 (한글 키)
      const lower = c.name.trim().toLowerCase();
      if (lower && !GENERIC_PK_NAMES.has(lower)) {
        const cands = (byPkName.get(lower) ?? []).filter((r) => r.table.id !== t.id);
        if (cands.length === 1) return linkTo(c, cands[0] as { table: ErdTable; pk: ErdColumn });
      }

      return c;
    });
    return { ...t, columns };
  });
}

/** 차원 추출 1건 — 키 칼럼들을 마스터로 분리(또는 기존 마스터에 연결). */
export interface DimensionOp {
  /** 만들 마스터 테이블명(생성 시). 기존 마스터가 있으면 무시되고 그 이름을 따름. */
  masterName: string;
  /** 마스터 PK 가 될 키 이름. */
  key: string;
  /** 키 타입(생성 시 PK 타입). */
  keyType: string;
  /** 마스터에 이름 칼럼(`<마스터>명`) 자리도 만들지 (기본 true). */
  withNameColumn?: boolean;
  /** 이 키를 FK 로 연결할 팩트 칼럼들. */
  sources: { tableId: string; columnId: string }[];
}

/**
 * 차원 추출 적용(순수) — 각 op 에 대해: 같은 PK 이름의 단일-PK 마스터가 이미 있으면 *연결만*,
 * 없으면 마스터 테이블을 *생성*(PK + 선택적 이름 칼럼)하고, sources 칼럼에 FK 를 건다.
 * FK 칼럼 타입은 마스터 PK 타입을 따르고 nullable 로(= linkTo 와 동일 규칙). PK 칼럼은 건너뜀.
 */
export function applyDimensions(
  tables: ErdTable[],
  ops: DimensionOp[],
): { tables: ErdTable[]; created: number } {
  let result = tables;
  const taken = new Set(result.map((t) => t.name.toLowerCase()));
  let created = 0;

  for (const op of ops) {
    const keyNorm = op.key.trim().toLowerCase();
    // 같은 PK 이름의 단일-PK 마스터가 정확히 1개면 그곳에 연결(중복 생성 방지).
    const existingMasters = result.filter((t) => {
      const pks = t.columns.filter((c) => c.pk);
      return pks.length === 1 && (pks[0] as ErdColumn).name.trim().toLowerCase() === keyNorm;
    });
    const existing = existingMasters.length === 1 ? existingMasters[0] : undefined;

    let masterName: string;
    let pkName: string;
    let pkType: string;

    if (existing) {
      const pk = existing.columns.find((c) => c.pk) as ErdColumn;
      masterName = existing.name;
      pkName = pk.name;
      pkType = pk.type;
    } else {
      const raw = op.masterName.trim() || op.key.trim() || 'dimension';
      let nm = raw;
      let n = 2;
      while (taken.has(nm.toLowerCase())) nm = `${raw}_${n++}`;
      taken.add(nm.toLowerCase());
      masterName = nm;
      pkName = op.key.trim() || 'id';
      pkType = op.keyType || 'TEXT';
      const cols = [newColumn({ name: pkName, type: pkType, pk: true, nullable: false })];
      if (op.withNameColumn !== false) {
        cols.push(newColumn({ name: `${nm}명`, type: 'TEXT', nullable: true }));
      }
      result = [...result, { id: uid(), name: nm, columns: cols, position: gridPosition(result.length) }];
      created += 1;
    }

    // sources 에 FK 연결 (tableId → columnId 집합).
    const byTable = new Map<string, Set<string>>();
    for (const s of op.sources) {
      const set = byTable.get(s.tableId) ?? new Set<string>();
      set.add(s.columnId);
      byTable.set(s.tableId, set);
    }
    result = result.map((t) => {
      const cols = byTable.get(t.id);
      if (!cols) return t;
      return {
        ...t,
        columns: t.columns.map((c) =>
          cols.has(c.id) && !c.pk
            ? { ...c, type: pkType, nullable: true, fk: { table: masterName, column: pkName } }
            : c,
        ),
      };
    });
  }

  return { tables: result, created };
}

interface DbDesignState {
  name: string;
  tables: ErdTable[];
  selectedTableId: string | null;
  dirty: boolean;

  setSelected: (id: string | null) => void;
  addTable: () => void;
  renameTable: (id: string, name: string) => void;
  setTableComment: (id: string, comment: string) => void;
  removeTable: (id: string) => void;
  moveTable: (id: string, position: { x: number; y: number }) => void;

  addColumn: (tableId: string) => void;
  updateColumn: (tableId: string, columnId: string, patch: Partial<ErdColumn>) => void;
  removeColumn: (tableId: string, columnId: string) => void;

  /** 캔버스 연결: source 테이블에 target PK 를 참조하는 FK 컬럼 추가. */
  connect: (sourceTableId: string, targetTableId: string) => void;

  /** 외부(엑셀 등) 테이블을 기존 설계에 누적 추가. 이름 충돌 시 _2…, 격자 배치, 옵션 자동 FK. 추가 수 반환. */
  importTables: (inputs: ImportTableInput[], opts?: { autoFk?: boolean }) => number;

  /** 한 칼럼을 차원 마스터로 분리(또는 기존 마스터에 연결) + FK. 수동(패널 버튼)용. */
  extractDimension: (
    tableId: string,
    columnId: string,
    opts?: { tableName?: string; withNameColumn?: boolean },
  ) => void;
  /** 도우미 제안(여러 건)을 일괄 적용. 생성된 마스터 수 반환. */
  applyDimensionSuggestions: (suggestions: DimensionSuggestion[]) => number;

  load: (design: ErdDesign) => void;
  serialize: () => ErdDesign;
  markSaved: () => void;
  /** 캔버스의 모든 테이블 삭제(설계명은 유지) — dirty 로 표시해 저장 시 빈 설계가 반영. */
  clearAll: () => void;
  reset: () => void;
}

export const useDbDesign = create<DbDesignState>((set, get) => ({
  name: 'dreamagent_data',
  tables: [],
  selectedTableId: null,
  dirty: false,

  setSelected: (id) => set({ selectedTableId: id }),

  addTable: () =>
    set((s) => {
      const n = s.tables.length;
      const t = newTable(`table_${n + 1}`, 80 + (n % 4) * 260, 80 + Math.floor(n / 4) * 220);
      return { tables: [...s.tables, t], selectedTableId: t.id, dirty: true };
    }),

  renameTable: (id, name) =>
    set((s) => {
      const oldName = s.tables.find((t) => t.id === id)?.name;
      return {
        tables: s.tables.map((t) => {
          const renamed = t.id === id ? { ...t, name } : t;
          // 이름이 바뀌면, 이 테이블을 참조하던 FK(어느 테이블이든)의 table 명도 갱신 — 끊김 방지.
          if (!oldName || oldName === name) return renamed;
          return {
            ...renamed,
            columns: renamed.columns.map((c) =>
              c.fk && c.fk.table === oldName ? { ...c, fk: { ...c.fk, table: name } } : c,
            ),
          };
        }),
        dirty: true,
      };
    }),

  setTableComment: (id, comment) =>
    set((s) => ({ tables: s.tables.map((t) => (t.id === id ? { ...t, comment } : t)), dirty: true })),

  removeTable: (id) =>
    set((s) => {
      const removedName = s.tables.find((x) => x.id === id)?.name;
      // 같은 이름의 다른 테이블이 남아있으면 그 테이블을 참조하는 FK 는 유효 — 정리하지 않는다.
      const stillExists = s.tables.some((t) => t.id !== id && t.name === removedName);
      return {
        tables: s.tables
          .filter((t) => t.id !== id)
          // 삭제된 테이블을 참조하던 FK 정리 (동명 생존 테이블이 없을 때만)
          .map((t) => ({
            ...t,
            columns: t.columns.map((c) =>
              !stillExists && c.fk && c.fk.table === removedName ? { ...c, fk: null } : c,
            ),
          })),
        selectedTableId: s.selectedTableId === id ? null : s.selectedTableId,
        dirty: true,
      };
    }),

  moveTable: (id, position) =>
    set((s) => ({ tables: s.tables.map((t) => (t.id === id ? { ...t, position } : t)), dirty: true })),

  addColumn: (tableId) =>
    set((s) => ({
      tables: s.tables.map((t) =>
        t.id === tableId ? { ...t, columns: [...t.columns, newColumn()] } : t,
      ),
      dirty: true,
    })),

  updateColumn: (tableId, columnId, patch) =>
    set((s) => ({
      tables: s.tables.map((t) =>
        t.id === tableId
          ? { ...t, columns: t.columns.map((c) => (c.id === columnId ? { ...c, ...patch } : c)) }
          : t,
      ),
      dirty: true,
    })),

  removeColumn: (tableId, columnId) =>
    set((s) => ({
      tables: s.tables.map((t) =>
        t.id === tableId ? { ...t, columns: t.columns.filter((c) => c.id !== columnId) } : t,
      ),
      dirty: true,
    })),

  connect: (sourceTableId, targetTableId) =>
    set((s) => {
      if (sourceTableId === targetTableId) return s;
      const src = s.tables.find((t) => t.id === sourceTableId);
      const tgt = s.tables.find((t) => t.id === targetTableId);
      if (!src || !tgt) return s;
      const tgtPk = tgt.columns.find((c) => c.pk) ?? tgt.columns[0];
      if (!tgtPk) return s;
      const colName = `${tgt.name}_${tgtPk.name}`;
      // 이미 같은 FK 가 있으면 중복 추가 안 함
      if (src.columns.some((c) => c.fk && c.fk.table === tgt.name && c.fk.column === tgtPk.name)) {
        return s;
      }
      const fkCol = newColumn({
        name: colName,
        type: tgtPk.type,
        nullable: true,
        fk: { table: tgt.name, column: tgtPk.name },
      });
      return {
        tables: s.tables.map((t) =>
          t.id === sourceTableId ? { ...t, columns: [...t.columns, fkCol] } : t,
        ),
        dirty: true,
      };
    }),

  importTables: (inputs, opts) => {
    if (!inputs.length) return 0;
    let addedCount = 0;
    set((s) => {
      const taken = new Set(s.tables.map((t) => t.name.toLowerCase()));
      const base = s.tables.length;
      const added: ErdTable[] = [];

      inputs.forEach((inp, i) => {
        const rawName = (inp.name || '').trim() || `table_${base + i + 1}`;
        let name = rawName;
        let n = 2;
        while (taken.has(name.toLowerCase())) name = `${rawName}_${n++}`;
        taken.add(name.toLowerCase());

        const cols = (inp.columns.length
          ? inp.columns
          : [{ name: 'id', type: 'UUID', pk: true, nullable: false }]
        ).map((c) =>
          newColumn({
            name: c.name || 'column',
            type: c.type || 'TEXT',
            pk: c.pk ?? false,
            nullable: c.nullable ?? !(c.pk ?? false),
            unique: c.unique ?? false,
            default: c.default ?? null,
          }),
        );
        // PK 미지정 시 'id' 컬럼을 PK 로 승격 (편의).
        if (!cols.some((c) => c.pk)) {
          const idCol = cols.find((c) => /^id$/i.test(c.name));
          if (idCol) {
            idCol.pk = true;
            idCol.nullable = false;
          }
        }

        added.push({
          id: uid(),
          name,
          comment: inp.comment,
          columns: cols,
          position: gridPosition(base + added.length),
        });
      });

      addedCount = added.length;
      const merged = [...s.tables, ...added];
      const tables = opts?.autoFk ? linkForeignKeys(merged, added) : merged;
      return {
        tables,
        dirty: true,
        selectedTableId: added[added.length - 1]?.id ?? s.selectedTableId,
      };
    });
    return addedCount;
  },

  extractDimension: (tableId, columnId, opts) =>
    set((s) => {
      const t = s.tables.find((x) => x.id === tableId);
      const c = t?.columns.find((x) => x.id === columnId);
      if (!t || !c || c.pk) return s;
      const op: DimensionOp = {
        masterName: opts?.tableName?.trim() || deriveMasterName(c.name),
        key: c.name,
        keyType: c.type,
        withNameColumn: opts?.withNameColumn ?? true,
        sources: [{ tableId, columnId }],
      };
      const { tables } = applyDimensions(s.tables, [op]);
      // 새 마스터를 선택(있으면) — 연결만 됐으면 선택 유지.
      const master = tables.find((x) => x.columns.some((mc) => mc.pk && mc.name === c.name));
      return { tables, selectedTableId: master?.id ?? s.selectedTableId, dirty: true };
    }),

  applyDimensionSuggestions: (suggestions) => {
    let created = 0;
    if (!suggestions.length) return 0;
    set((s) => {
      const ops: DimensionOp[] = suggestions.map((g) => ({
        masterName: g.masterName,
        key: g.key,
        keyType: g.keyType,
        withNameColumn: true,
        sources: g.sources.map((x) => ({ tableId: x.tableId, columnId: x.columnId })),
      }));
      const res = applyDimensions(s.tables, ops);
      created = res.created;
      return { tables: res.tables, dirty: true };
    });
    return created;
  },

  load: (design) =>
    set({
      name: design.name || 'dreamagent_data',
      tables: design.tables ?? [],
      selectedTableId: null,
      dirty: false,
    }),

  serialize: () => {
    const s = get();
    return { name: s.name, tables: s.tables };
  },

  markSaved: () => set({ dirty: false }),

  clearAll: () => set({ tables: [], selectedTableId: null, dirty: true }),

  reset: () => set({ name: 'dreamagent_data', tables: [], selectedTableId: null, dirty: false }),
}));
