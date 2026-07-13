/**
 * 차원 추출 도우미 — 제안 로직 박제.
 * 핵심: 키 접미사 칼럼 → 생성 제안 / 기존 단일-PK 마스터 일치 → 연결 제안 /
 *       일반 속성(담당자 등)·일반명(코드)·이미 FK 인 칼럼은 제외 / 같은 키는 한 제안으로 묶음.
 */
import { describe, expect, it } from 'vitest';
import { suggestDimensions, deriveMasterName, isKeyLike } from './dimensions';
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
const byKey = (s: ReturnType<typeof suggestDimensions>, key: string) =>
  s.find((x) => x.key === key);

describe('deriveMasterName', () => {
  it('키 접미사 제거 → 엔티티명', () => {
    expect(deriveMasterName('거래처ID')).toBe('거래처');
    expect(deriveMasterName('customer_id')).toBe('customer');
    expect(deriveMasterName('품목코드')).toBe('품목');
    expect(deriveMasterName('지점번호')).toBe('지점');
  });
  it('접미사 없으면 그대로', () => {
    expect(deriveMasterName('사번')).toBe('사번');
    expect(deriveMasterName('품목')).toBe('품목');
  });
});

describe('isKeyLike', () => {
  it('키 접미사 인정 / 일반명·속성 제외', () => {
    expect(isKeyLike('거래처ID')).toBe(true);
    expect(isKeyLike('customer_id')).toBe(true);
    expect(isKeyLike('품목코드')).toBe(true);
    expect(isKeyLike('id')).toBe(false); // 일반명 단독
    expect(isKeyLike('코드')).toBe(false);
    expect(isKeyLike('담당자')).toBe(false);
    expect(isKeyLike('품목')).toBe(false);
  });
});

describe('suggestDimensions', () => {
  it('D1 — 키 접미사 칼럼, 마스터 없음 → 생성 제안', () => {
    const fact = tbl('실적', [col('거래처ID'), col('담당자'), col('기간'), col('값', { type: 'INTEGER' })]);
    const out = suggestDimensions([fact]);
    expect(out).toHaveLength(1);
    const s = out[0]!;
    expect(s.key).toBe('거래처ID');
    expect(s.masterName).toBe('거래처');
    expect(s.existing).toBeNull();
    expect(s.sources).toEqual([{ tableId: 't_실적', tableName: '실적', columnId: expect.any(String) }]);
  });

  it('D2 — 기존 단일-PK 마스터와 일치 → 연결 제안(생성 아님)', () => {
    const master = tbl('거래처', [col('거래처ID', { pk: true }), col('거래처명')]);
    const fact = tbl('실적', [col('거래처ID'), col('값', { type: 'INTEGER' })]);
    const out = suggestDimensions([master, fact]);
    const s = byKey(out, '거래처ID')!;
    expect(s.existing).toBe('거래처');
    expect(s.masterName).toBe('거래처');
    // 마스터 자신의 PK 는 소스가 아님(팩트의 거래처ID 만)
    expect(s.sources).toEqual([{ tableId: 't_실적', tableName: '실적', columnId: expect.any(String) }]);
  });

  it('D3 — 일반 속성/일반명/값 칼럼은 제안 없음', () => {
    const fact = tbl('실적', [col('담당자'), col('코드'), col('기간'), col('값', { type: 'INTEGER' })]);
    expect(suggestDimensions([fact])).toHaveLength(0);
  });

  it('D4 — 여러 테이블에 흩어진 같은 키 → 한 제안으로 묶고 소스 2개', () => {
    const sales = tbl('실적', [col('거래처ID'), col('값', { type: 'INTEGER' })]);
    const ret = tbl('반품', [col('거래처ID'), col('수량', { type: 'INTEGER' })]);
    const out = suggestDimensions([sales, ret]);
    const s = byKey(out, '거래처ID')!;
    expect(s.existing).toBeNull();
    expect(s.sources).toHaveLength(2);
    expect(s.sources.map((x) => x.tableName).sort()).toEqual(['반품', '실적']);
  });

  it('D5 — 이미 FK 인 칼럼은 제외', () => {
    const fact = tbl('실적', [col('거래처ID', { fk: { table: '거래처', column: '거래처ID' } }), col('값')]);
    expect(suggestDimensions([fact])).toHaveLength(0);
  });

  it('D6 — 동명 PK 마스터 2개(모호) → 연결 안 함(existing null)', () => {
    const m1 = tbl('거래처A', [col('거래처ID', { pk: true })]);
    const m2 = tbl('거래처B', [col('거래처ID', { pk: true })]);
    const fact = tbl('실적', [col('거래처ID'), col('값')]);
    const out = suggestDimensions([m1, m2, fact]);
    const s = byKey(out, '거래처ID')!;
    expect(s.existing).toBeNull(); // 모호 → 자동 연결 회피
  });

  it('D7 — 마스터가 있으면 비(非)키명 칼럼도 연결 후보로 포함', () => {
    // 직원.사번(PK) 마스터 존재 → 실적.사번(키 접미사 아님)도 연결 제안.
    const emp = tbl('직원', [col('사번', { pk: true }), col('이름')]);
    const fact = tbl('실적', [col('사번'), col('값')]);
    const out = suggestDimensions([emp, fact]);
    const s = byKey(out, '사번')!;
    expect(s.existing).toBe('직원');
    expect(s.sources).toEqual([{ tableId: 't_실적', tableName: '실적', columnId: expect.any(String) }]);
  });

  it('D8 — 생성 제안이 연결 제안보다 앞', () => {
    const master = tbl('거래처', [col('거래처ID', { pk: true })]);
    const fact = tbl('실적', [col('거래처ID'), col('품목ID')]);
    const out = suggestDimensions([master, fact]);
    expect(out[0]!.existing).toBeNull(); // 품목ID(생성)
    expect(out[0]!.key).toBe('품목ID');
    expect(out[1]!.existing).toBe('거래처'); // 거래처ID(연결)
  });
});
