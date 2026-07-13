/**
 * 지표 발견기 박제 — 팩트 분류 + 후보 규칙(KPI/추이/Top-N/차원×시간/성장) + SQL 초안.
 */
import { describe, expect, it } from 'vitest';
import { suggestMetrics, metricToSql, isFactTable, type Metric } from './metrics';
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

// 실적 팩트: 사번/거래처ID/품목(FK) + 담당자 + 년월(시간) + 값(측정)
const 실적 = tbl('실적', [
  col('사번', { fk: { table: '인사', column: '사번' } }),
  col('담당자'),
  col('거래처ID', { fk: { table: '거래처', column: '거래처ID' } }),
  col('품목', { fk: { table: '품목', column: '품목' } }),
  col('년월'),
  col('값', { type: 'INTEGER' }),
]);

const byKind = (ms: Metric[], kind: string) => ms.filter((m) => m.kind === kind);

describe('isFactTable', () => {
  it('측정값+차원 있으면 팩트, 마스터(텍스트+PK)는 아님', () => {
    expect(isFactTable(실적)).toBe(true);
    const 거래처 = tbl('거래처', [col('거래처ID', { pk: true }), col('원장명'), col('지역구')]);
    expect(isFactTable(거래처)).toBe(false);
  });
  it('숫자 측정값 있는 마스터(인사)는 팩트로도 인정', () => {
    const 인사 = tbl('인사', [
      col('사번', { pk: true }),
      col('지점'),
      col('기본급', { type: 'BIGINT' }),
    ]);
    expect(isFactTable(인사)).toBe(true);
  });
});

describe('suggestMetrics', () => {
  const ms = suggestMetrics([실적]);

  it('KPI 총합 1건', () => {
    const kpi = byKind(ms, 'kpi');
    expect(kpi).toHaveLength(1);
    expect(kpi[0]!.name).toBe('총 값');
    expect(kpi[0]!.aggregate).toBe('SUM');
    expect(kpi[0]!.dimensions).toEqual([]);
  });

  it('시간 추이 + 성장 (년월 인식)', () => {
    expect(byKind(ms, 'trend')).toHaveLength(1);
    expect(byKind(ms, 'trend')[0]!.dimensions).toEqual([{ column: '년월', time: true }]);
    expect(byKind(ms, 'trend')[0]!.chart).toBe('line');
    expect(byKind(ms, 'growth')).toHaveLength(1);
  });

  it('차원별 Top-N — 차원 4개(사번/담당자/거래처ID/품목)', () => {
    const bd = byKind(ms, 'breakdown');
    expect(bd.map((m) => m.dimensions[0]!.column).sort()).toEqual(
      ['거래처ID', '담당자', '사번', '품목'].sort(),
    );
    expect(bd[0]!.chart).toBe('bar');
    expect(bd[0]!.limit).toBe(10);
    expect(bd[0]!.sort).toBe('desc');
  });

  it('차원×시간 추이 — FK 차원만(담당자 텍스트 제외)', () => {
    const tb = byKind(ms, 'trend_by');
    expect(tb.map((m) => m.dimensions[0]!.column).sort()).toEqual(['거래처ID', '사번', '품목'].sort());
    // 담당자(텍스트, FK 아님)는 다계열 추이에서 제외
    expect(tb.some((m) => m.dimensions[0]!.column === '담당자')).toBe(false);
  });

  it('측정값/시간 없는 순수 마스터는 제안 0', () => {
    const 거래처 = tbl('거래처', [col('거래처ID', { pk: true }), col('원장명')]);
    expect(suggestMetrics([거래처])).toHaveLength(0);
  });

  it('이름에 "월" 든 측정값(월방문횟수·월평균사용예산)은 시간축이 아니라 측정값', () => {
    const 거래처자료 = tbl('거래처자료', [
      col('거래처ID', { fk: { table: '거래처', column: '거래처ID' } }),
      col('월'), // 진짜 시간축(202212)
      col('매출', { type: 'INTEGER' }),
      col('월방문횟수', { type: 'INTEGER' }), // 측정값 — '월' 부분일치에 안 걸려야
      col('월평균사용예산', { type: 'INTEGER' }), // 측정값
    ]);
    const ms = suggestMetrics([거래처자료]);
    // 월방문횟수가 KPI(측정값)로 나오고, breakdown 차원으로는 안 나옴
    expect(ms.some((m) => m.kind === 'kpi' && m.measure === '월방문횟수')).toBe(true);
    expect(ms.some((m) => m.kind === 'kpi' && m.measure === '월평균사용예산')).toBe(true);
    expect(ms.some((m) => m.kind === 'breakdown' && m.dimensions[0]!.column === '월방문횟수')).toBe(false);
    // 시간 추이는 '월'(진짜 시간축) 기준으로만
    const trends = byKind(ms, 'trend');
    expect(trends.every((m) => m.dimensions[0]!.column === '월')).toBe(true);
  });
});

describe('metricToSql', () => {
  const ms = suggestMetrics([실적]);
  const find = (kind: string) => ms.find((m) => m.kind === kind)!;

  it('KPI → 단순 집계', () => {
    expect(metricToSql(find('kpi'))).toBe('SELECT SUM("값") AS "sum_값"\nFROM "실적"');
  });

  it('추이 → GROUP BY 시간 + 정렬', () => {
    const sql = metricToSql(find('trend'));
    expect(sql).toContain('GROUP BY "년월"');
    expect(sql).toContain('ORDER BY "년월" ASC');
  });

  it('Top-N → GROUP BY 차원 + ORDER BY 값 DESC + LIMIT', () => {
    const bd = ms.find((m) => m.kind === 'breakdown' && m.dimensions[0]!.column === '거래처ID')!;
    const sql = metricToSql(bd);
    expect(sql).toContain('GROUP BY "거래처ID"');
    expect(sql).toContain('ORDER BY "sum_값" DESC');
    expect(sql).toContain('LIMIT 10');
  });

  it('성장 → LAG 윈도우', () => {
    const sql = metricToSql(find('growth'));
    expect(sql).toContain('LAG(SUM("값")) OVER (ORDER BY "년월")');
    expect(sql).toContain('"전기간대비"');
  });
});
