/**
 * unpivot 박제 — 연속 기간 런 감지 + 가로→세로 접기.
 */
import { describe, expect, it } from 'vitest';
import { detectPeriodRuns, unpivotDerived } from './unpivot';
import type { DerivedColumn } from './parseWorkbook';
import type { ColumnType } from './store';

const C = (...names: string[]): DerivedColumn[] =>
  names.map((name) => ({ name, type: 'TEXT', samples: 1 }));

/** 첫 strong(없으면 첫) 런을 접고 결과 컬럼명 반환. */
function fold(colNames: string[]): string[] {
  const cols = C(...colNames);
  const runs = detectPeriodRuns(cols);
  const r = runs.find((x) => x.strong) ?? runs[0];
  if (!r) return colNames;
  return unpivotDerived({ columns: cols, rowCount: 0 }, r).columns.map((c) => c.name);
}

/** 202212 부터 24개월 (2022-12 ~ 2024-11). */
function months24(): string[] {
  const out = ['202212'];
  for (let m = 1; m <= 12; m++) out.push(`2023${String(m).padStart(2, '0')}`);
  for (let m = 1; m <= 11; m++) out.push(`2024${String(m).padStart(2, '0')}`);
  return out;
}

describe('detectPeriodRuns / unpivot', () => {
  it('U1 — 24× yyyymm, 그룹 없음 → 년월/값', () => {
    const cols = C('사번', '담당자', '거래처ID', '품목', ...months24());
    const runs = detectPeriodRuns(cols);
    expect(runs).toHaveLength(1);
    expect(runs[0]).toMatchObject({
      start: 4,
      end: 27,
      length: 24,
      kind: 'yyyymm',
      group: null,
      strong: true,
      periodName: '년월',
      valueName: '값',
    });
    expect(fold(['사번', '담당자', '거래처ID', '품목', ...months24()])).toEqual([
      '사번',
      '담당자',
      '거래처ID',
      '품목',
      '년월',
      '값',
    ]);
  });

  it('U2 — 그룹 유지 → 값 칼럼명=실적', () => {
    const names = ['사번', '담당자', '거래처ID', '품목'];
    for (const m of ['202212', '202301', '202302', '202303', '202304', '202305', '202306'])
      names.push(`실적_${m}`);
    const runs = detectPeriodRuns(C(...names));
    expect(runs).toHaveLength(1);
    expect(runs[0]).toMatchObject({ length: 7, kind: 'yyyymm', group: '실적', strong: true, valueName: '실적' });
    expect(fold(names)).toEqual(['사번', '담당자', '거래처ID', '품목', '년월', '실적']);
  });

  it('U3 — 구분자 yyyy-mm', () => {
    const names = ['지점', '2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06'];
    const runs = detectPeriodRuns(C(...names));
    expect(runs).toHaveLength(1);
    expect(runs[0]).toMatchObject({ length: 6, kind: 'yyyy_sep_mm', strong: true });
    expect(fold(names)).toEqual(['지점', '년월', '값']);
  });

  it('U4 — 비기간 칼럼이 런을 둘로 분리', () => {
    const runs = detectPeriodRuns(
      C('사번', '202301', '202302', '202303', '비고', '202401', '202402', '202403', '202404', '202405', '202406'),
    );
    expect(runs).toHaveLength(2);
    expect(runs[0]).toMatchObject({ start: 1, end: 3, length: 3, strong: false });
    expect(runs[1]).toMatchObject({ start: 5, end: 10, length: 6, strong: true });
  });

  it('U5 — kind 다르면 병합 안 됨 + 짧은 연도 런 무시', () => {
    const runs = detectPeriodRuns(C('품목', '2021', '2022', '202301', '202302', '202303', '202304'));
    expect(runs).toHaveLength(1);
    expect(runs[0]).toMatchObject({ start: 3, end: 6, length: 4, kind: 'yyyymm', strong: false });
  });

  it('U6 — 런 없음: ID/잘못된 월/짧음', () => {
    expect(detectPeriodRuns(C('사번', '담당자', '거래처ID', '품목', '금액', '수량'))).toEqual([]);
    expect(detectPeriodRuns(C('id', '100001', '100002', '100003'))).toEqual([]);
    expect(detectPeriodRuns(C('a', '202213', '202214', '202215'))).toEqual([]);
  });

  it('U7 — 한글 월 라벨', () => {
    const names = ['대리점', '1월', '2월', '3월', '4월', '5월', '6월', '7월'];
    const runs = detectPeriodRuns(C(...names));
    expect(runs).toHaveLength(1);
    expect(runs[0]).toMatchObject({ length: 7, kind: 'month_label', strong: true, periodName: '기간' });
    expect(fold(names)).toEqual(['대리점', '기간', '값']);
  });

  it('U8 — 런이 중간(끝이 아님)', () => {
    const names = ['사번', '202301', '202302', '202303', '202304', '202305', '202306', '담당자', '품목'];
    const runs = detectPeriodRuns(C(...names));
    expect(runs).toHaveLength(1);
    expect(runs[0]).toMatchObject({ start: 1, end: 6, length: 6, strong: true });
    expect(fold(names)).toEqual(['사번', '담당자', '품목', '년월', '값']);
  });

  it('U9 — 값 타입은 런 칼럼 타입을 넓혀서 사용 (넓은 런에서도 안 좁아짐)', () => {
    const cols: DerivedColumn[] = [
      { name: '사번', type: 'VARCHAR(255)', samples: 200 },
      { name: '담당자', type: 'VARCHAR(255)', samples: 200 },
      ...['실적_202212', '실적_202301', '실적_202302', '실적_202303', '실적_202304', '실적_202305'].map(
        (name): DerivedColumn => ({ name, type: 'INTEGER' as ColumnType, samples: 200 }),
      ),
    ];
    const r = detectPeriodRuns(cols).find((x) => x.strong);
    expect(r).toBeTruthy();
    const out = unpivotDerived({ columns: cols, rowCount: 200 }, r!);
    expect(out.columns.map((c) => c.name)).toEqual(['사번', '담당자', '년월', '실적']);
    expect(out.columns.at(-2)).toMatchObject({ name: '년월', type: 'VARCHAR(255)' });
    expect(out.columns.at(-1)).toMatchObject({ name: '실적', type: 'INTEGER' });
  });

  it('U10 — 런에 NUMERIC 이 섞이면 값 타입을 NUMERIC 으로 넓힘 (소수 절단 방지)', () => {
    const cols: DerivedColumn[] = [
      { name: '품목', type: 'VARCHAR(255)', samples: 100 },
      { name: '실적_202301', type: 'INTEGER', samples: 100 },
      { name: '실적_202302', type: 'NUMERIC', samples: 100 },
      { name: '실적_202303', type: 'INTEGER', samples: 100 },
      { name: '실적_202304', type: 'INTEGER', samples: 100 },
      { name: '실적_202305', type: 'INTEGER', samples: 100 },
      { name: '실적_202306', type: 'INTEGER', samples: 100 },
    ];
    const r = detectPeriodRuns(cols).find((x) => x.strong);
    const out = unpivotDerived({ columns: cols, rowCount: 100 }, r!);
    expect(out.columns.at(-1)).toMatchObject({ name: '실적', type: 'NUMERIC' });
  });

  it('U11 — 다른 그룹 접두사(실적/목표)는 별개 런으로 분리 (값 섞임 방지)', () => {
    const names = ['사번'];
    for (const m of ['202301', '202302', '202303', '202304', '202305', '202306'])
      names.push(`실적_${m}`);
    for (const m of ['202301', '202302', '202303', '202304', '202305', '202306'])
      names.push(`목표_${m}`);
    const runs = detectPeriodRuns(C(...names));
    expect(runs).toHaveLength(2);
    expect(runs[0]).toMatchObject({ group: '실적', valueName: '실적', strong: true });
    expect(runs[1]).toMatchObject({ group: '목표', valueName: '목표', strong: true });
  });
});
