/**
 * parseWorkbook — 엑셀/CSV 파일 → ERD 테이블 후보.
 *
 * 시트마다 테이블 1개. "첫 줄=컬럼" 고정 규칙이 아니라 **헤더 행 자동 감지**:
 *  - 위쪽 제목/설명 행은 건너뛰고, "헤더처럼 생긴 행"을 점수로 선택.
 *  - 병합셀 기반 **계층(다단) 헤더**(예: [고객정보][주문정보] / 고객ID·이름)도 합쳐 컬럼명 구성.
 *  - 데이터 행을 샘플링해 타입(INTEGER/DATE/BOOLEAN/...) 추론.
 * 파싱(원본 행 추출)은 1회, 컬럼 도출(deriveTable)은 순수함수 — 미리보기에서 헤더 행을
 * 바꿀 때마다 즉시 재계산할 수 있다. SheetJS(xlsx)는 사용 시점에 동적 import (번들 경량).
 */
import type { ColumnType } from './store';

export type CellValue = string | number | boolean | Date | null;

/** 배열 좌표(원점 정규화 후)로 표현한 병합 범위. */
export interface MergeRange {
  r1: number;
  c1: number;
  r2: number;
  c2: number;
}

export interface SheetSource {
  id: string;
  fileName: string;
  sheetName: string;
  /** 시트 원본 행 (행 인덱스 = 병합 좌표와 정렬됨). */
  rows: CellValue[][];
  merges: MergeRange[];
  /** 자동 감지된 헤더 시작 행 / 행 수. */
  detected: { start: number; count: number };
  suggestedName: string;
}

export interface DerivedColumn {
  name: string;
  type: ColumnType;
  /** 타입 추론에 쓰인 비어있지 않은 샘플 수. */
  samples: number;
}

export interface DerivedTable {
  columns: DerivedColumn[];
  rowCount: number;
}

const uid = (): string =>
  globalThis.crypto?.randomUUID?.() ?? `src_${Math.random().toString(36).slice(2)}`;

const GENERIC_SHEET = /^(sheet|시트|sheet1|sheet_?\d+|시트\d+)$/i;

export const isBlank = (v: CellValue): boolean =>
  v == null || (typeof v === 'string' && v.trim() === '');

function hasTime(d: Date): boolean {
  return d.getHours() !== 0 || d.getMinutes() !== 0 || d.getSeconds() !== 0;
}

/** 파일들을 읽어 시트별 SheetSource 로 펼친다. (xlsx 동적 import) */
export async function readWorkbooks(files: File[]): Promise<SheetSource[]> {
  const XLSX = await import('xlsx');
  const out: SheetSource[] = [];

  for (const file of files) {
    let wb: import('xlsx').WorkBook;
    try {
      const buf = await file.arrayBuffer();
      wb = XLSX.read(buf, { type: 'array', cellDates: true });
    } catch {
      continue; // 깨진/비엑셀 파일은 건너뜀
    }
    const baseName = file.name.replace(/\.[^.]+$/, '');

    for (const sheetName of wb.SheetNames) {
      const ws = wb.Sheets[sheetName];
      if (!ws || !ws['!ref']) continue;

      const range = XLSX.utils.decode_range(ws['!ref']);
      const originR = range.s.r;
      const originC = range.s.c;

      // header:1 → 행 배열. blankrows:true 로 병합 좌표와 인덱스 정렬 유지.
      const raw = XLSX.utils.sheet_to_json<CellValue[]>(ws, {
        header: 1,
        raw: true,
        defval: null,
        blankrows: true,
      });
      // 원점 보정: 시트가 A1 이 아닌 곳에서 시작하면 좌측 빈 컬럼만큼 패딩 보존됨(header:1 이 처리).
      const rows = raw.map((r) => (Array.isArray(r) ? r : []));
      if (rows.length === 0) continue;

      const merges: MergeRange[] = (ws['!merges'] ?? []).map((m) => ({
        r1: m.s.r - originR,
        c1: m.s.c - originC,
        r2: m.e.r - originR,
        c2: m.e.c - originC,
      }));

      // 선두 빈 컬럼 트림 — 시트 범위가 좌측 빈 컬럼을 포함하면 phantom col_N 이 생긴다.
      let minCol = Infinity;
      for (const row of rows) {
        for (let c = 0; c < row.length; c++) {
          if (!isBlank(row[c] ?? null)) {
            if (c < minCol) minCol = c;
            break;
          }
        }
      }
      if (Number.isFinite(minCol) && minCol > 0) {
        for (let i = 0; i < rows.length; i++) rows[i] = (rows[i] ?? []).slice(minCol);
        for (const m of merges) {
          m.c1 = Math.max(0, m.c1 - minCol);
          m.c2 = Math.max(0, m.c2 - minCol);
        }
      }

      const detected = detectHeader(rows, merges);
      const generic = GENERIC_SHEET.test(sheetName.trim());
      const suggestedName =
        generic && wb.SheetNames.length === 1 ? baseName : sheetName || baseName;

      out.push({
        id: uid(),
        fileName: file.name,
        sheetName,
        rows,
        merges,
        detected,
        suggestedName: cleanName([suggestedName]) || baseName || 'table',
      });
    }
  }
  return out;
}

/** 병합 해소: (r,c) 가 병합 범위 안이면 좌상단 값을 돌려준다. */
function resolveCell(rows: CellValue[][], merges: MergeRange[], r: number, c: number): CellValue {
  for (const m of merges) {
    if (r >= m.r1 && r <= m.r2 && c >= m.c1 && c <= m.c2) {
      return rows[m.r1]?.[m.c1] ?? null;
    }
  }
  return rows[r]?.[c] ?? null;
}

function rowWidth(rows: CellValue[][], from: number, to: number): number {
  let w = 0;
  for (let r = from; r <= to && r < rows.length; r++) {
    const row = rows[r];
    if (Array.isArray(row)) w = Math.max(w, row.length);
  }
  return w;
}

/** 한 행이 "헤더처럼 보이는" 정도를 점수화. 높을수록 헤더 후보. */
function scoreHeaderRow(rows: CellValue[][], r: number): number {
  const row = rows[r];
  if (!Array.isArray(row)) return -1;
  const cells = row;
  const width = Math.max(cells.length, 1);
  let nonEmpty = 0;
  let strings = 0;
  let numbers = 0;
  let shorts = 0;
  for (const v of cells) {
    if (isBlank(v)) continue;
    nonEmpty++;
    if (typeof v === 'string') {
      strings++;
      if (v.trim().length <= 40) shorts++;
    } else if (typeof v === 'number') {
      numbers++;
    }
  }
  if (nonEmpty === 0) return -1;
  // 단일 셀만 채워진 넓은 행 = 제목행 → 강한 감점.
  if (nonEmpty === 1 && width >= 3) return 0.1;

  const fill = nonEmpty / width;
  let score = fill * 2 + strings / width + shorts / width - (numbers / width) * 1.5;

  // 바로 아래에 데이터로 보이는 행(숫자/날짜 포함, 또는 충분히 채워짐)이 있으면 가산.
  const next = nextNonEmptyRow(rows, r + 1);
  if (next >= 0) {
    const nr = rows[next] ?? [];
    const hasData = nr.some((v) => typeof v === 'number' || v instanceof Date || !isBlank(v));
    if (hasData) score += 0.5;
  } else {
    score -= 0.3; // 아래에 아무것도 없으면 헤더로서 약함
  }
  return score;
}

function nextNonEmptyRow(rows: CellValue[][], from: number): number {
  for (let r = from; r < rows.length; r++) {
    const row = rows[r];
    if (Array.isArray(row) && row.some((v) => !isBlank(v))) return r;
  }
  return -1;
}

const HEADER_BAND_MAX = 3; // 헤더 밴드 최대 행 수
const HEADER_TOP_SLACK = 3; // top0 부터 이 범위 내 가로병합만 그룹으로 인정

function isTitleRow(rows: CellValue[][], r: number, width: number): boolean {
  const row = rows[r] ?? [];
  let n = 0;
  for (let c = 0; c < width; c++) if (!isBlank(row[c] ?? null)) n++;
  return n === 1 && width >= 3;
}

/**
 * 헤더 시작 행 + 행 수 추정.
 *  - 첫 내용 행(top0)에 앵커된 "가로 병합 그룹"이 있으면 → 그 그룹들(contiguous) + 바로 아래
 *    리프 행을 헤더 밴드로. **가로 병합만** 사용하므로 데이터 영역의 세로 병합·카테고리 셀이나
 *    헤더 아래 배너 병합에 흔들리지 않는다(월=텍스트/숫자 무관).
 *  - 그런 그룹이 없으면 → 단일 헤더 휴리스틱(legacyDetectHeader).
 */
export function detectHeader(
  rows: CellValue[][],
  merges: MergeRange[],
): { start: number; count: number } {
  if (rows.length === 0) return { start: 0, count: 1 };

  // 폭: 앞쪽 구간에서 가장 오른쪽 비어있지 않은 컬럼.
  const scan = Math.min(rows.length, 60);
  let width = 1;
  for (let r = 0; r < scan; r++) {
    const row = rows[r] ?? [];
    for (let c = row.length - 1; c >= 0; c--) {
      if (!isBlank(row[c] ?? null)) {
        width = Math.max(width, c + 1);
        break;
      }
    }
  }

  // 첫 내용 행.
  let top0 = -1;
  for (let r = 0; r < scan; r++) {
    if ((rows[r] ?? []).some((v) => !isBlank(v ?? null))) {
      top0 = r;
      break;
    }
  }
  if (top0 < 0) return { start: 0, count: 1 };

  // top0 에 앵커된 가로 병합(그룹 라벨)이 있어야 다단 헤더로 인정.
  const hMerges = merges.filter(
    (m) => m.c2 > m.c1 && m.r1 >= top0 && m.r1 <= top0 + HEADER_TOP_SLACK,
  );
  if (hMerges.some((m) => m.r1 === top0)) {
    // top0 부터 contiguous 한 가로 병합들의 최하단(배너처럼 떨어진 병합은 제외).
    let groupBottom = top0;
    let changed = true;
    while (changed) {
      changed = false;
      for (const m of hMerges) {
        if (m.r1 <= groupBottom + 1 && m.r2 > groupBottom) {
          groupBottom = m.r2;
          changed = true;
        }
      }
    }
    // 리프(라벨) 행 = 그룹 병합 바로 아래 한 행.
    const end = Math.min(groupBottom + 1, rows.length - 1);
    let start = top0;
    while (start < end && isTitleRow(rows, start, width)) start += 1;
    let count = end - start + 1;
    if (count < 1) count = 1;
    if (count > HEADER_BAND_MAX) {
      start = end - (HEADER_BAND_MAX - 1);
      count = HEADER_BAND_MAX;
    }
    return { start: Math.max(0, start), count };
  }

  return legacyDetectHeader(rows);
}

/** 단일 헤더 휴리스틱 (상단 병합이 없을 때 fallback) — 점수 최고 행 + 다단 추정. */
function legacyDetectHeader(rows: CellValue[][]): { start: number; count: number } {
  const limit = Math.min(rows.length, 15);
  let best = -1;
  let bestScore = -Infinity;
  for (let r = 0; r < limit; r++) {
    const s = scoreHeaderRow(rows, r);
    if (s > bestScore) {
      bestScore = s;
      best = r;
    }
  }
  if (best < 0) best = nextNonEmptyRow(rows, 0);
  if (best < 0) return { start: 0, count: 1 };

  // 다단(계층) 헤더 감지: 헤더 행에 빈칸이 있고 다음 행이 그것을 채우는(=하위 라벨) 형태면 2행.
  let count = 1;
  const nextR = best + 1;
  if (nextR < rows.length) {
    const headRow = rows[best] ?? [];
    const width = rowWidth(rows, best, nextR);
    const headBlanks = countBlanks(headRow, width);
    const nextScore = scoreHeaderRow(rows, nextR);
    const nextIsHeaderLike = nextScore > 0.6 && !rows[nextR]?.some((v) => v instanceof Date);
    if (nextIsHeaderLike && headBlanks > 0) count = 2;
  }
  return { start: best, count };
}

function countBlanks(row: CellValue[], width: number): number {
  let n = 0;
  for (let c = 0; c < width; c++) if (isBlank(row[c] ?? null)) n++;
  return n;
}

function cleanName(parts: CellValue[]): string {
  const cleaned: string[] = [];
  for (const p of parts) {
    if (isBlank(p)) continue;
    const s = String(p).trim().replace(/\s+/g, '_').replace(/[.,;:"'`]/g, '');
    if (!s) continue;
    if (cleaned[cleaned.length - 1] === s) continue; // 세로 병합으로 같은 값 중복 제거
    cleaned.push(s);
  }
  return cleaned.join('_');
}

export function inferType(values: CellValue[]): ColumnType {
  const vals = values.filter((v) => !isBlank(v)).slice(0, 100);
  if (vals.length === 0) return 'TEXT';

  let allBool = true;
  let allDate = true;
  let allNum = true;
  let anyTime = false;
  let allInt = true;
  let bigInt = false;
  let maxLen = 0;

  for (const v of vals) {
    if (typeof v !== 'boolean') allBool = false;
    if (v instanceof Date) {
      if (hasTime(v)) anyTime = true;
    } else {
      allDate = false;
    }
    if (typeof v === 'number') {
      if (!Number.isInteger(v)) allInt = false;
      if (Math.abs(v) >= 2 ** 31) bigInt = true;
    } else {
      allNum = false;
    }
    if (typeof v === 'string') maxLen = Math.max(maxLen, v.length);
  }

  if (allBool) return 'BOOLEAN';
  if (allDate) return anyTime ? 'TIMESTAMPTZ' : 'DATE';
  if (allNum) return allInt ? (bigInt ? 'BIGINT' : 'INTEGER') : 'NUMERIC';
  return maxLen > 255 ? 'TEXT' : 'VARCHAR(255)';
}

/** 헤더 밴드(병합 해소)에서 컬럼 폭 + 이름을 도출. deriveTable/extractRows 공유 — 정렬 보장. */
function deriveColumnNames(
  source: SheetSource,
  start: number,
  count: number,
): { width: number; names: string[] } {
  const { rows, merges } = source;
  const dataStart = start + count;

  // 컬럼 폭: 헤더 밴드 + 데이터 일부에서 가장 오른쪽 비어있지 않은 컬럼까지.
  const scanTo = Math.min(rows.length - 1, dataStart + 50);
  let width = 0;
  for (let r = start; r <= scanTo; r++) {
    const row = rows[r];
    if (!Array.isArray(row)) continue;
    for (let c = row.length - 1; c >= 0; c--) {
      if (!isBlank(row[c] ?? null)) {
        width = Math.max(width, c + 1);
        break;
      }
    }
  }
  if (width === 0) width = rowWidth(rows, start, dataStart);

  const seen = new Map<string, number>();
  const names: string[] = [];
  for (let c = 0; c < width; c++) {
    const parts: CellValue[] = [];
    for (let r = start; r < dataStart; r++) parts.push(resolveCell(rows, merges, r, c));
    let name = cleanName(parts);
    if (!name) name = `col_${c + 1}`;
    const lower = name.toLowerCase();
    const prev = seen.get(lower);
    if (prev) {
      seen.set(lower, prev + 1);
      name = `${name}_${prev + 1}`;
    } else {
      seen.set(lower, 1);
    }
    names.push(name);
  }
  return { width, names };
}

/**
 * 헤더 시작/행 수가 주어졌을 때 컬럼 + 타입을 도출. (순수함수 — 미리보기 재계산용)
 */
export function deriveTable(
  source: SheetSource,
  headerStart: number,
  headerCount: number,
): DerivedTable {
  const { rows } = source;
  const start = Math.max(0, Math.min(headerStart, rows.length - 1));
  const count = Math.max(1, Math.min(headerCount, 3));
  const dataStart = start + count;
  const { width, names } = deriveColumnNames(source, start, count);

  const columns: DerivedColumn[] = [];
  for (let c = 0; c < width; c++) {
    // 데이터 샘플 수집(해당 컬럼 세로) → 타입 추론.
    const sample: CellValue[] = [];
    for (let r = dataStart; r < rows.length && sample.length < 100; r++) {
      sample.push(rows[r]?.[c] ?? null);
    }
    const nonEmpty = sample.filter((v) => !isBlank(v));
    columns.push({ name: names[c] ?? `col_${c + 1}`, type: inferType(sample), samples: nonEmpty.length });
  }

  let rowCount = 0;
  for (let r = dataStart; r < rows.length; r++) {
    if (rows[r]?.some((v) => !isBlank(v))) rowCount++;
  }

  return { columns, rowCount };
}

/**
 * 실제 데이터 행을 추출 — DB 빌드용. deriveTable 과 동일한 컬럼 도출(이름·순서·폭)을 쓰므로
 * 반환 rows 는 deriveTable().columns 와 위치가 1:1 정렬된다. 완전 빈 행은 건너뜀.
 */
export function extractRows(
  source: SheetSource,
  headerStart: number,
  headerCount: number,
): { columns: string[]; rows: CellValue[][] } {
  const { rows } = source;
  const start = Math.max(0, Math.min(headerStart, rows.length - 1));
  const count = Math.max(1, Math.min(headerCount, 3));
  const dataStart = start + count;
  const { width, names } = deriveColumnNames(source, start, count);

  const out: CellValue[][] = [];
  for (let r = dataStart; r < rows.length; r++) {
    const row = rows[r];
    if (!Array.isArray(row) || !row.some((v) => !isBlank(v))) continue;
    const rec: CellValue[] = [];
    for (let c = 0; c < width; c++) rec.push(row[c] ?? null);
    out.push(rec);
  }
  return { columns: names, rows: out };
}
