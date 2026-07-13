/**
 * unpivot — 연속 "기간" 칼럼(202212~202411 등) 감지 + 가로→세로 스키마 변환.
 *
 * 엑셀의 가로형(달마다 칼럼)을 DB가 원하는 세로형 스키마로: 반복 기간 칼럼 N개를
 * [기간, 값] 2칼럼으로 접는다(스키마 레벨 — 실제 데이터 행 이동은 없음).
 * 강한 런(>=6)은 미리보기에서 기본 ON, 3~5는 감지만 하고 사용자가 선택.
 * 순수함수 — ExcelImportDialog 가 헤더 보정/토글 시 즉시 재계산.
 */
import type { ColumnType } from './store';
import type { CellValue, DerivedColumn, DerivedTable } from './parseWorkbook';

export type PeriodKind = 'yyyymm' | 'yyyy_sep_mm' | 'quarter' | 'yyyy' | 'month_label';

export interface PeriodRun {
  start: number; // 런 첫 칼럼 인덱스
  end: number; // 런 마지막 칼럼 인덱스(포함)
  length: number;
  kind: PeriodKind;
  group: string | null; // 2단 헤더 그룹명(실적 등) — 값 칼럼 이름에 사용
  strong: boolean; // 기본 ON 여부
  periodName: string; // 기간 칼럼 이름 후보
  valueName: string; // 값 칼럼 이름 후보
  periodTypeOptions: ColumnType[]; // [0] = 기본 타입
}

const MIN_RUN = 3;
const STRONG_RUN = 6;
const MIN_YEAR_RUN = 4; // 단순 연도(yyyy)는 더 긴 런만 인정(오탐 방지)

const RE_YYYYMM = /^(19|20)\d{2}(0[1-9]|1[0-2])$/;
const RE_YYYY_SEP_MM = /^(19|20)\d{2}[-./](0[1-9]|1[0-2])$/;
const RE_QUARTER = /^((19|20)\d{2}[-_ ]?Q[1-4]|Q[1-4][-_ ]?(19|20)\d{2})$/i;
const RE_YYYY = /^(19|20)\d{2}$/;
const RE_MONTH_LABEL =
  /^((0?[1-9]|1[0-2])월|M(0?[1-9]|1[0-2])|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)$/i;

/** 컬럼명의 마지막 세그먼트(그룹 접두사 뒤) — "실적_202212" → "202212". */
function leafOf(name: string): string {
  const i = name.lastIndexOf('_');
  return i >= 0 ? name.slice(i + 1) : name;
}

/** 컬럼명의 그룹 접두사(리프 앞) — "실적_202212" → "실적", "202212" → null. */
function prefixOf(name: string): string | null {
  const i = name.lastIndexOf('_');
  return i >= 0 ? name.slice(0, i) : null;
}

function classifyPeriod(leaf: string): PeriodKind | null {
  const s = leaf.trim();
  if (RE_YYYYMM.test(s)) return 'yyyymm';
  if (RE_YYYY_SEP_MM.test(s)) return 'yyyy_sep_mm';
  if (RE_QUARTER.test(s)) return 'quarter';
  if (RE_YYYY.test(s)) return 'yyyy';
  if (RE_MONTH_LABEL.test(s)) return 'month_label';
  return null;
}

/** 런 칼럼들이 공통 그룹 접두사를 가지면 그 접두사, 아니면 null. */
function sharedGroup(names: string[]): string | null {
  let group: string | null = null;
  for (let i = 0; i < names.length; i++) {
    const n = names[i] ?? '';
    const idx = n.lastIndexOf('_');
    const g = idx >= 0 ? n.slice(0, idx) : null;
    if (i === 0) group = g;
    else if (g !== group) return null;
  }
  return group;
}

/** 컬럼 목록에서 연속 기간 런들을 감지. (동일 kind 연속 + 비기간 칼럼이 런을 끊음) */
export function detectPeriodRuns(columns: DerivedColumn[]): PeriodRun[] {
  const runs: PeriodRun[] = [];
  let i = 0;
  while (i < columns.length) {
    const col = columns[i];
    const kind = col ? classifyPeriod(leafOf(col.name)) : null;
    if (!col || !kind) {
      i += 1;
      continue;
    }
    // 런은 같은 kind + 같은 그룹 접두사일 때만 이어진다 (실적_/목표_ 블록이 합쳐지지 않도록).
    const startPrefix = prefixOf(col.name);
    let j = i + 1;
    while (j < columns.length) {
      const c2 = columns[j];
      if (!c2 || classifyPeriod(leafOf(c2.name)) !== kind || prefixOf(c2.name) !== startPrefix) break;
      j += 1;
    }
    const length = j - i;
    const minForKind = kind === 'yyyy' ? MIN_YEAR_RUN : MIN_RUN;
    if (length >= minForKind) {
      const names = columns.slice(i, j).map((c) => c.name);
      const group = sharedGroup(names);
      const periodName = kind === 'yyyymm' || kind === 'yyyy_sep_mm' ? '년월' : '기간';
      const periodTypeOptions: ColumnType[] =
        kind === 'yyyymm' ? ['VARCHAR(255)', 'INTEGER'] : ['VARCHAR(255)'];
      runs.push({
        start: i,
        end: j - 1,
        length,
        kind,
        group,
        strong: length >= STRONG_RUN,
        periodName,
        valueName: group ?? '값',
        periodTypeOptions,
      });
    }
    i = j;
  }
  return runs;
}

function dedupe(name: string, used: Set<string>): string {
  let n = name;
  let i = 2;
  while (used.has(n.toLowerCase())) n = `${name}_${i++}`;
  used.add(n.toLowerCase());
  return n;
}

const NUMERIC_RANK: Partial<Record<ColumnType, number>> = {
  INTEGER: 1,
  BIGINT: 2,
  FLOAT: 3,
  NUMERIC: 4,
};
const DATE_TYPES = new Set<ColumnType>(['DATE', 'TIMESTAMPTZ']);
const TEXT_TYPES = new Set<ColumnType>(['VARCHAR(255)', 'TEXT']);

/** 런 칼럼들의 타입을 하나로 — 같은 계열이면 가장 넓은 타입(예: INTEGER+NUMERIC→NUMERIC), 섞이면 TEXT. */
function widenValueType(types: ColumnType[]): ColumnType {
  if (types.length === 0) return 'TEXT';
  const uniq = [...new Set(types)];
  if (uniq.length === 1) return uniq[0] as ColumnType;
  if (uniq.every((t) => t in NUMERIC_RANK)) {
    return uniq.reduce((a, b) => ((NUMERIC_RANK[b] ?? 0) > (NUMERIC_RANK[a] ?? 0) ? b : a));
  }
  if (uniq.every((t) => DATE_TYPES.has(t))) return uniq.includes('TIMESTAMPTZ') ? 'TIMESTAMPTZ' : 'DATE';
  if (uniq.every((t) => TEXT_TYPES.has(t))) return uniq.includes('TEXT') ? 'TEXT' : 'VARCHAR(255)';
  return 'TEXT';
}

/**
 * 런을 [기간, 값] 2칼럼으로 접은 스키마. 값 타입은 미리 도출된 base 칼럼 타입을 넓혀서 사용
 * (런 전체 칼럼을 보므로, 넓은 런에서 일부 행만 샘플링해 타입이 좁아지던 문제 없음).
 * keep(접히지 않는 칼럼)은 순서 보존 — 키 칼럼(사번/거래처ID/품목 등)이 살아남아 이후 자동 FK 와 합쳐진다.
 */
export function unpivotDerived(
  derived: DerivedTable,
  run: PeriodRun,
  override?: { periodType?: ColumnType },
): DerivedTable {
  const keep = derived.columns.filter((_, i) => i < run.start || i > run.end);
  const runCols = derived.columns.slice(run.start, run.end + 1);
  const valueType = widenValueType(runCols.map((c) => c.type));
  const periodType: ColumnType = override?.periodType ?? run.periodTypeOptions[0] ?? 'VARCHAR(255)';

  const used = new Set(keep.map((c) => c.name.toLowerCase()));
  const periodName = dedupe(run.periodName, used);
  const valueName = dedupe(run.valueName, used);
  const valueSamples = runCols.reduce((s, c) => s + c.samples, 0);

  return {
    columns: [
      ...keep,
      { name: periodName, type: periodType, samples: run.length },
      { name: valueName, type: valueType, samples: valueSamples },
    ],
    rowCount: derived.rowCount * run.length,
  };
}

/**
 * 데이터 행을 [기간, 값]으로 접는다(DB 빌드용). unpivotDerived 와 동일한 컬럼 구성/이름을 내므로
 * 결과는 그 스키마와 위치 정렬된다. columns/rows 는 extractRows 출력(파생 컬럼 정렬).
 * 기간 값 = 런 컬럼명의 리프(예: "실적_202212" → "202212"), 값 = 해당 셀.
 */
export function unpivotRows(
  columns: string[],
  rows: CellValue[][],
  run: PeriodRun,
): { columns: string[]; rows: CellValue[][] } {
  const keepIdx: number[] = [];
  for (let i = 0; i < columns.length; i++) if (i < run.start || i > run.end) keepIdx.push(i);
  const runIdx: number[] = [];
  for (let i = run.start; i <= run.end; i++) runIdx.push(i);

  const keepNames = keepIdx.map((i) => columns[i] ?? `col_${i + 1}`);
  const used = new Set(keepNames.map((n) => n.toLowerCase()));
  const periodName = dedupe(run.periodName, used);
  const valueName = dedupe(run.valueName, used);
  const periodLabels = runIdx.map((i) => leafOf(columns[i] ?? ''));

  const out: CellValue[][] = [];
  for (const row of rows) {
    for (let k = 0; k < runIdx.length; k++) {
      const rec: CellValue[] = keepIdx.map((i) => row[i] ?? null);
      rec.push(periodLabels[k] ?? null);
      rec.push(row[runIdx[k] as number] ?? null);
      out.push(rec);
    }
  }
  return { columns: [...keepNames, periodName, valueName], rows: out };
}
