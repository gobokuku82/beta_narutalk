/**
 * DB설계 store — ERD 스키마 모델 (Zustand).
 *
 * 시스템 → DB설계 페이지의 단일 진실 소스. 테이블/컬럼/관계(FK)를 보유하고
 * 캔버스(노드=테이블, 엣지=FK)·편집 패널·DDL 생성기가 공유한다.
 * 영속: api/hooks/useDbDesign (백엔드 GET/PUT). 출력: ddl.ts (PostgreSQL DDL).
 */
import { create } from 'zustand';

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

  load: (design: ErdDesign) => void;
  serialize: () => ErdDesign;
  markSaved: () => void;
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
    set((s) => ({ tables: s.tables.map((t) => (t.id === id ? { ...t, name } : t)), dirty: true })),

  setTableComment: (id, comment) =>
    set((s) => ({ tables: s.tables.map((t) => (t.id === id ? { ...t, comment } : t)), dirty: true })),

  removeTable: (id) =>
    set((s) => ({
      tables: s.tables
        .filter((t) => t.id !== id)
        // 삭제된 테이블을 참조하던 FK 정리
        .map((t) => ({
          ...t,
          columns: t.columns.map((c) =>
            c.fk && c.fk.table === s.tables.find((x) => x.id === id)?.name ? { ...c, fk: null } : c,
          ),
        })),
      selectedTableId: s.selectedTableId === id ? null : s.selectedTableId,
      dirty: true,
    })),

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

  reset: () => set({ name: 'dreamagent_data', tables: [], selectedTableId: null, dirty: false }),
}));
