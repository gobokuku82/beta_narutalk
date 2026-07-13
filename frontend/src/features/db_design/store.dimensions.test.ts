/**
 * 차원 추출 적용 박제 — applyDimensions(순수) + 스토어 액션(extractDimension / applyDimensionSuggestions).
 * 핵심: 마스터 생성(PK + 이름칼럼) + 소스 FK 연결 / 기존 마스터엔 연결만 / 이름 충돌 _2 / 이름칼럼 토글.
 */
import { describe, expect, it } from 'vitest';
import { applyDimensions, useDbDesign, type DimensionOp } from './store';
import { suggestDimensions } from './dimensions';
import type { ErdColumn, ErdTable, ErdFk } from './store';

let seq = 0;
function col(name: string, opts: { pk?: boolean; type?: string; fk?: ErdFk } = {}): ErdColumn {
  return {
    id: `c${seq++}`,
    name,
    type: opts.type ?? 'TEXT',
    pk: opts.pk ?? false,
    nullable: !opts.pk,
    unique: false,
    default: null,
    fk: opts.fk ?? null,
  };
}
function tbl(name: string, columns: ErdColumn[]): ErdTable {
  return { id: `t_${name}`, name, columns, position: { x: 0, y: 0 } };
}
const findTable = (tables: ErdTable[], name: string) => tables.find((t) => t.name === name);
const fkOf = (tables: ErdTable[], table: string, colName: string) =>
  findTable(tables, table)?.columns.find((c) => c.name === colName)?.fk;

describe('applyDimensions', () => {
  it('E1 — 마스터 생성(PK + 이름칼럼) + 소스 FK', () => {
    const fact = tbl('실적', [col('거래처ID'), col('값', { type: 'INTEGER' })]);
    const op: DimensionOp = {
      masterName: '거래처',
      key: '거래처ID',
      keyType: 'TEXT',
      sources: [{ tableId: 't_실적', columnId: fact.columns[0]!.id }],
    };
    const { tables, created } = applyDimensions([fact], [op]);
    expect(created).toBe(1);
    const master = findTable(tables, '거래처')!;
    expect(master.columns.map((c) => [c.name, c.pk])).toEqual([
      ['거래처ID', true],
      ['거래처명', false],
    ]);
    expect(fkOf(tables, '실적', '거래처ID')).toEqual({ table: '거래처', column: '거래처ID' });
  });

  it('E2 — 기존 단일-PK 마스터엔 연결만(생성 0)', () => {
    const master = tbl('거래처', [col('거래처ID', { pk: true, type: 'VARCHAR(255)' }), col('거래처명')]);
    const fact = tbl('실적', [col('거래처ID', { type: 'TEXT' }), col('값')]);
    const op: DimensionOp = {
      masterName: '거래처_new', // 무시되어야 함 — 기존 거래처에 연결
      key: '거래처ID',
      keyType: 'TEXT',
      sources: [{ tableId: 't_실적', columnId: fact.columns[0]!.id }],
    };
    const { tables, created } = applyDimensions([master, fact], [op]);
    expect(created).toBe(0);
    expect(tables.filter((t) => t.name.startsWith('거래처'))).toHaveLength(1);
    expect(fkOf(tables, '실적', '거래처ID')).toEqual({ table: '거래처', column: '거래처ID' });
    // FK 칼럼 타입은 마스터 PK 타입 승계
    expect(findTable(tables, '실적')!.columns[0]!.type).toBe('VARCHAR(255)');
  });

  it('E3 — 마스터명 충돌 시 _2', () => {
    const dup = tbl('거래처', [col('id', { pk: true })]);
    const fact = tbl('실적', [col('거래처ID'), col('값')]);
    const op: DimensionOp = {
      masterName: '거래처',
      key: '거래처ID',
      keyType: 'TEXT',
      sources: [{ tableId: 't_실적', columnId: fact.columns[0]!.id }],
    };
    const { tables } = applyDimensions([dup, fact], [op]);
    // 기존 '거래처'(PK=id) 는 거래처ID 와 PK 이름이 달라 연결 대상 아님 → 새로 '거래처_2' 생성
    expect(findTable(tables, '거래처_2')).toBeTruthy();
    expect(fkOf(tables, '실적', '거래처ID')).toEqual({ table: '거래처_2', column: '거래처ID' });
  });

  it('E4 — withNameColumn=false → PK만', () => {
    const fact = tbl('실적', [col('품목코드'), col('값')]);
    const op: DimensionOp = {
      masterName: '품목',
      key: '품목코드',
      keyType: 'TEXT',
      withNameColumn: false,
      sources: [{ tableId: 't_실적', columnId: fact.columns[0]!.id }],
    };
    const { tables } = applyDimensions([fact], [op]);
    expect(findTable(tables, '품목')!.columns.map((c) => c.name)).toEqual(['품목코드']);
  });

  it('E5 — 한 op 의 소스가 여러 테이블이면 모두 연결', () => {
    const a = tbl('실적', [col('거래처ID'), col('값')]);
    const b = tbl('반품', [col('거래처ID'), col('수량')]);
    const op: DimensionOp = {
      masterName: '거래처',
      key: '거래처ID',
      keyType: 'TEXT',
      sources: [
        { tableId: 't_실적', columnId: a.columns[0]!.id },
        { tableId: 't_반품', columnId: b.columns[0]!.id },
      ],
    };
    const { tables } = applyDimensions([a, b], [op]);
    expect(fkOf(tables, '실적', '거래처ID')).toEqual({ table: '거래처', column: '거래처ID' });
    expect(fkOf(tables, '반품', '거래처ID')).toEqual({ table: '거래처', column: '거래처ID' });
  });
});

describe('store.extractDimension', () => {
  it('패널 단일 추출 — 마스터 생성 + FK + 마스터 선택', () => {
    const fact = tbl('실적', [col('거래처ID'), col('값')]);
    useDbDesign.getState().load({ name: 't', tables: [fact] });
    useDbDesign.getState().extractDimension('t_실적', fact.columns[0]!.id);
    const st = useDbDesign.getState();
    const master = st.tables.find((t) => t.name === '거래처');
    expect(master).toBeTruthy();
    expect(st.selectedTableId).toBe(master!.id);
    expect(fkOf(st.tables, '실적', '거래처ID')).toEqual({ table: '거래처', column: '거래처ID' });
    useDbDesign.getState().reset();
  });

  it('PK 칼럼엔 동작 안 함', () => {
    const fact = tbl('실적', [col('사번', { pk: true }), col('값')]);
    useDbDesign.getState().load({ name: 't', tables: [fact] });
    useDbDesign.getState().extractDimension('t_실적', fact.columns[0]!.id);
    expect(useDbDesign.getState().tables).toHaveLength(1); // 새 마스터 없음
    useDbDesign.getState().reset();
  });
});

describe('store.applyDimensionSuggestions', () => {
  it('도우미 제안 일괄 적용 — 생성 수 반환 + 모든 FK 연결', () => {
    const fact = tbl('실적', [col('거래처ID'), col('품목ID'), col('값', { type: 'INTEGER' })]);
    useDbDesign.getState().load({ name: 't', tables: [fact] });
    const suggestions = suggestDimensions(useDbDesign.getState().tables);
    const created = useDbDesign.getState().applyDimensionSuggestions(suggestions);
    expect(created).toBe(2);
    const st = useDbDesign.getState();
    expect(fkOf(st.tables, '실적', '거래처ID')).toEqual({ table: '거래처', column: '거래처ID' });
    expect(fkOf(st.tables, '실적', '품목ID')).toEqual({ table: '품목', column: '품목ID' });
    useDbDesign.getState().reset();
  });
});
