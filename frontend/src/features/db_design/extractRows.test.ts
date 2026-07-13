/**
 * 행 추출 + 행 언피벗 박제 — DB 빌드 데이터 경로.
 * 핵심: extractRows 의 컬럼/순서가 deriveTable 과 1:1 정렬(위치 적재 안전) +
 *       2단 병합 헤더에서 이름 합성 + unpivotRows 가 [기간,값]으로 바르게 펼침.
 */
import { describe, expect, it } from 'vitest';
import { deriveTable, extractRows, type SheetSource, type CellValue } from './parseWorkbook';
import { detectPeriodRuns, unpivotRows } from './unpivot';

function source(rows: CellValue[][], merges: SheetSource['merges'] = [], detected = { start: 0, count: 1 }): SheetSource {
  return { id: 's', fileName: 'f.xlsx', sheetName: 'S', rows, merges, detected, suggestedName: 'S' };
}

describe('extractRows', () => {
  it('단일 헤더 — 컬럼/행 정렬 + 빈 행 스킵', () => {
    const s = source([
      ['사번', '값'],
      ['MR-1', 10],
      [null, null], // 빈 행 → 스킵
      ['MR-2', 20],
    ]);
    const { columns, rows } = extractRows(s, 0, 1);
    expect(columns).toEqual(['사번', '값']);
    expect(rows).toEqual([
      ['MR-1', 10],
      ['MR-2', 20],
    ]);
  });

  it('deriveTable 컬럼명과 정확히 같은 순서(위치 적재 보장)', () => {
    const s = source([
      ['사번', '거래처ID', '값'],
      ['MR-1', 'A의원', 10],
    ]);
    const cols = deriveTable(s, 0, 1).columns.map((c) => c.name);
    expect(extractRows(s, 0, 1).columns).toEqual(cols);
  });

  it('2단 병합 헤더 — 그룹_리프 이름 합성 + 행 정렬', () => {
    // row0: [_, _, 실적(2..3 병합)] / row1: [사번, 거래처ID, 202212, 202301]
    const s = source(
      [
        [null, null, '실적', null],
        ['사번', '거래처ID', '202212', '202301'],
        ['MR-1', 'A의원', 100, 200],
      ],
      [{ r1: 0, c1: 2, r2: 0, c2: 3 }],
      { start: 0, count: 2 },
    );
    const { columns, rows } = extractRows(s, 0, 2);
    expect(columns).toEqual(['사번', '거래처ID', '실적_202212', '실적_202301']);
    expect(rows).toEqual([['MR-1', 'A의원', 100, 200]]);
  });
});

describe('unpivotRows', () => {
  it('가로 월(strong run) → [년월, 값] 세로로 펼침', () => {
    const months = ['202212', '202301', '202302', '202303', '202304', '202305'];
    const s = source([['사번', '거래처ID', ...months], ['MR-1', 'A의원', 10, 20, 30, 40, 50, 60]]);
    const base = deriveTable(s, 0, 1);
    const run = detectPeriodRuns(base.columns).find((r) => r.strong)!;
    const ext = extractRows(s, 0, 1);
    const { columns, rows } = unpivotRows(ext.columns, ext.rows, run);

    expect(columns).toEqual(['사번', '거래처ID', '년월', '값']);
    expect(rows).toHaveLength(6); // 1행 × 6개월
    expect(rows[0]).toEqual(['MR-1', 'A의원', '202212', 10]);
    expect(rows[5]).toEqual(['MR-1', 'A의원', '202305', 60]);
  });

  it('2단 그룹 헤더(실적) → 값 칼럼명이 그룹명', () => {
    const months = ['202212', '202301', '202302', '202303', '202304', '202305'];
    const s = source(
      [
        [null, ...months.map(() => '실적'), null].slice(0, 7), // placeholder; 병합으로 대체
        ['사번', ...months],
        ['MR-1', 10, 20, 30, 40, 50, 60],
      ],
      [{ r1: 0, c1: 1, r2: 0, c2: 6 }],
      { start: 0, count: 2 },
    );
    const base = deriveTable(s, 0, 2);
    const run = detectPeriodRuns(base.columns).find((r) => r.strong)!;
    const ext = extractRows(s, 0, 2);
    const { columns } = unpivotRows(ext.columns, ext.rows, run);
    expect(columns).toEqual(['사번', '년월', '실적']);
  });
});
