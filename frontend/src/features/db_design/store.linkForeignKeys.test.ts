/**
 * 자동 FK v2 박제 — 규칙1(xxx_id) + 규칙2(컬럼명=다른 표 PK명, 한글 키).
 * 후보는 단일 PK 테이블만, 규칙2는 일반명 제외 + 후보 1개일 때만(오연결 방지).
 */
import { describe, expect, it } from 'vitest';
import { linkForeignKeys, useDbDesign } from './store';
import type { ErdColumn, ErdTable, ErdFk } from './store';

let seq = 0;
function col(
  name: string,
  opts: { pk?: boolean; type?: string; fk?: ErdFk } = {},
): ErdColumn {
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
function fkOf(tables: ErdTable[], tableName: string, colName: string): ErdFk | null | undefined {
  return tables.find((t) => t.name === tableName)?.columns.find((c) => c.name === colName)?.fk;
}

describe('linkForeignKeys v2', () => {
  it('F1 — 한글 정확명 키 (사번/거래처ID/품목)', () => {
    const emp = tbl('직원', [col('사번', { pk: true }), col('담당자')]);
    const cust = tbl('거래처', [col('거래처ID', { pk: true }), col('거래처명')]);
    const item = tbl('품목', [col('품목', { pk: true }), col('품목명')]);
    const fact = tbl('실적', [
      col('사번'),
      col('담당자'),
      col('거래처ID'),
      col('품목'),
      col('기간'),
      col('값'),
    ]);
    const out = linkForeignKeys([emp, cust, item, fact], [fact]);
    expect(fkOf(out, '실적', '사번')).toEqual({ table: '직원', column: '사번' });
    expect(fkOf(out, '실적', '거래처ID')).toEqual({ table: '거래처', column: '거래처ID' });
    expect(fkOf(out, '실적', '품목')).toEqual({ table: '품목', column: '품목' });
    expect(fkOf(out, '실적', '담당자')).toBeNull();
    expect(fkOf(out, '실적', '기간')).toBeNull();
  });

  it('F2 — 고전 xxx_id (규칙1 회귀)', () => {
    const customers = tbl('customers', [col('id', { pk: true, type: 'UUID' }), col('name')]);
    const orders = tbl('orders', [col('id', { pk: true, type: 'UUID' }), col('customer_id'), col('total')]);
    const out = linkForeignKeys([customers, orders], [orders]);
    expect(fkOf(out, 'orders', 'customer_id')).toEqual({ table: 'customers', column: 'id' });
    const fkCol = out.find((t) => t.name === 'orders')?.columns.find((c) => c.name === 'customer_id');
    expect(fkCol?.type).toBe('UUID'); // 참조 PK 타입 승계
    expect(fkOf(out, 'orders', 'id')).toBeNull();
    expect(fkOf(out, 'orders', 'total')).toBeNull();
  });

  it('F3 — 일반명 id 는 교차 연결 안 함', () => {
    const a = tbl('a', [col('id', { pk: true, type: 'UUID' }), col('label')]);
    const b = tbl('b', [col('id', { pk: true, type: 'UUID' }), col('note')]);
    const out = linkForeignKeys([a, b], [b]);
    expect(fkOf(out, 'b', 'id')).toBeNull();
    expect(fkOf(out, 'b', 'note')).toBeNull();
  });

  it('F4 — 모호하거나 일반명 → 건너뜀', () => {
    const region = tbl('region', [col('code', { pk: true }), col('region_name')]);
    const product = tbl('product', [col('code', { pk: true }), col('product_name')]);
    const sales = tbl('sales', [col('code'), col('amount')]);
    const out = linkForeignKeys([region, product, sales], [sales]);
    expect(fkOf(out, 'sales', 'code')).toBeNull();
  });

  it('F5 — 복합 PK 테이블은 FK 대상 아님', () => {
    const membership = tbl('membership', [
      col('user_id', { pk: true }),
      col('group_id', { pk: true }),
      col('role'),
    ]);
    const log = tbl('log', [col('membership'), col('ts')]);
    const out = linkForeignKeys([membership, log], [log]);
    expect(fkOf(out, 'log', 'membership')).toBeNull();
  });

  it('F6 — 기존 fk 보존 + 비대상 테이블 불변', () => {
    const emp = tbl('직원', [col('사번', { pk: true }), col('담당자')]);
    const preset: ErdFk = { table: '직원', column: '사번' };
    const fact = tbl('실적', [col('사번', { fk: preset }), col('담당자')]);
    const out = linkForeignKeys([emp, fact], [fact]);
    expect(fkOf(out, '실적', '사번')).toEqual(preset); // 변경 없음
    expect(fkOf(out, '직원', '담당자')).toBeNull(); // 비대상 불변
  });

  it('F7 — 키 아닌 공통 칼럼은 무반응', () => {
    const emp = tbl('직원', [col('사번', { pk: true }), col('담당자')]);
    const fact = tbl('실적', [col('사번'), col('담당자')]);
    const out = linkForeignKeys([emp, fact], [fact]);
    expect(fkOf(out, '실적', '사번')).toEqual({ table: '직원', column: '사번' });
    expect(fkOf(out, '실적', '담당자')).toBeNull();
  });

  it('F8 — 규칙1 동명 정규화 충돌(customer/customers) → 연결 안 함', () => {
    const customer = tbl('customer', [col('id', { pk: true, type: 'UUID' }), col('name')]);
    const customers = tbl('customers', [col('id', { pk: true, type: 'BIGINT' }), col('name')]);
    const orders = tbl('orders', [col('id', { pk: true }), col('customer_id')]);
    const out = linkForeignKeys([customer, customers, orders], [orders]);
    expect(fkOf(out, 'orders', 'customer_id')).toBeNull(); // 후보 2개 → 비결정 방지
  });

  it('F9 — 한글 일반명(코드)은 규칙2에서 제외', () => {
    const item = tbl('상품', [col('코드', { pk: true }), col('상품명')]);
    const order = tbl('주문', [col('코드'), col('수량')]);
    const out = linkForeignKeys([item, order], [order]);
    expect(fkOf(out, '주문', '코드')).toBeNull();
  });
});

describe('removeTable FK cleanup', () => {
  it('N2 — 동명 테이블 삭제 시 생존 동명 테이블의 FK 보존', () => {
    const dupA: ErdTable = {
      id: 'dupA',
      name: 'dup',
      columns: [col('id', { pk: true })],
      position: { x: 0, y: 0 },
    };
    const dupB: ErdTable = {
      id: 'dupB',
      name: 'dup',
      columns: [col('id', { pk: true })],
      position: { x: 0, y: 0 },
    };
    const ref: ErdTable = {
      id: 'ref',
      name: 'ref',
      columns: [col('dup_id', { fk: { table: 'dup', column: 'id' } })],
      position: { x: 0, y: 0 },
    };
    useDbDesign.getState().load({ name: 't', tables: [dupA, dupB, ref] });
    useDbDesign.getState().removeTable('dupA');
    const fk = useDbDesign.getState().tables.find((t) => t.id === 'ref')?.columns[0]?.fk;
    expect(fk).toEqual({ table: 'dup', column: 'id' }); // dupB 생존 → 정리 안 함
    useDbDesign.getState().reset();
  });
});

describe('renameTable FK preservation', () => {
  it('테이블 이름 변경 시, 그 테이블을 참조하던 FK 의 table 명도 갱신(끊김 방지)', () => {
    const master: ErdTable = {
      id: 'M',
      name: '거래처',
      columns: [col('거래처ID', { pk: true })],
      position: { x: 0, y: 0 },
    };
    const fact: ErdTable = {
      id: 'F',
      name: '실적',
      columns: [col('거래처ID', { fk: { table: '거래처', column: '거래처ID' } })],
      position: { x: 0, y: 0 },
    };
    useDbDesign.getState().load({ name: 't', tables: [master, fact] });
    useDbDesign.getState().renameTable('M', '거래처마스터');
    const fk = useDbDesign.getState().tables.find((t) => t.id === 'F')?.columns[0]?.fk;
    expect(fk).toEqual({ table: '거래처마스터', column: '거래처ID' }); // 옛 이름 → 새 이름
    useDbDesign.getState().reset();
  });
});

describe('clearAll', () => {
  it('모든 테이블 삭제 · 설계명 유지 · dirty=true (저장 반영용)', () => {
    const t = tbl('직원', [col('사번', { pk: true })]);
    useDbDesign.getState().load({ name: '내설계', tables: [t] });
    useDbDesign.getState().setSelected('t_직원');
    useDbDesign.getState().clearAll();
    const s = useDbDesign.getState();
    expect(s.tables).toEqual([]);
    expect(s.selectedTableId).toBeNull();
    expect(s.name).toBe('내설계'); // 설계명은 유지
    expect(s.dirty).toBe(true);
    useDbDesign.getState().reset();
  });
});
