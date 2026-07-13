/**
 * detectHeader v2 + deriveTable 이름 도출 박제.
 *
 * 상단 병합 구조로 다단 헤더를 잡고(월이 텍스트/숫자든 무관), 데이터 행을 헤더로 흡수하지 않는다.
 * 병합이 없으면 단일 헤더 휴리스틱(legacy)로 폴백. 두 실제 파일(FILE1 균일 2단, FILE2 혼합 계층) 포함.
 */
import { describe, expect, it } from 'vitest';
import {
  detectHeader,
  deriveTable,
  type CellValue,
  type MergeRange,
  type SheetSource,
} from './parseWorkbook';

const M = (r1: number, c1: number, r2: number, c2: number): MergeRange => ({ r1, c1, r2, c2 });

function stub(rows: CellValue[][], merges: MergeRange[]): SheetSource {
  return {
    id: 't',
    fileName: 'f.xlsx',
    sheetName: 's',
    rows,
    merges,
    detected: { start: 0, count: 1 },
    suggestedName: 't',
  };
}

function run(rows: CellValue[][], merges: MergeRange[] = []) {
  const detect = detectHeader(rows, merges);
  const cols = deriveTable(stub(rows, merges), detect.start, detect.count).columns.map((c) => c.name);
  return { detect, cols };
}

describe('detectHeader v2', () => {
  it('H1 — FILE1 균일 2단 헤더 (그룹 병합 + 리프)', () => {
    const rows: CellValue[][] = [
      ['퍼스널', null, '세일즈', null, '실적', null],
      ['사번', '담당자', '거래처ID', '품목', 202212, 202301],
      ['MR-01022', '정예준', '강서', '가스몬', 55473, 27101],
      ['MR-01023', '김철수', '서초', '타이레놀', 40094, 40404],
      ['MR-01024', '이영희', '강남', '아스피린', 66014, 73209],
    ];
    const merges = [M(0, 0, 0, 1), M(0, 2, 0, 3), M(0, 4, 0, 5)];
    const { detect, cols } = run(rows, merges);
    expect(detect).toEqual({ start: 0, count: 2 });
    expect(cols).toEqual([
      '퍼스널_사번',
      '퍼스널_담당자',
      '세일즈_거래처ID',
      '세일즈_품목',
      '실적_202212',
      '실적_202301',
    ]);
  });

  it('H2 — FILE2 혼합 계층 (월=텍스트)', () => {
    const rows: CellValue[][] = [
      ['사번', '담당자', '거래처ID', '품목', '실적', null],
      [null, null, null, null, '202212', '202301'],
      ['MR-01022', '정예준', '강서', '가스몬', 55473, 27101],
      ['MR-01023', '김철수', '서초', '타이레놀', 40094, 40404],
    ];
    const merges = [M(0, 0, 1, 0), M(0, 1, 1, 1), M(0, 2, 1, 2), M(0, 3, 1, 3), M(0, 4, 0, 5)];
    const { detect, cols } = run(rows, merges);
    expect(detect).toEqual({ start: 0, count: 2 });
    expect(cols).toEqual(['사번', '담당자', '거래처ID', '품목', '실적_202212', '실적_202301']);
  });

  it('H3 — FILE2 혼합 계층 (월=숫자)', () => {
    const rows: CellValue[][] = [
      ['사번', '담당자', '거래처ID', '품목', '실적', null],
      [null, null, null, null, 202212, 202301],
      ['MR-01022', '정예준', '강서', '가스몬', 55473, 27101],
      ['MR-01023', '김철수', '서초', '타이레놀', 40094, 40404],
    ];
    const merges = [M(0, 0, 1, 0), M(0, 1, 1, 1), M(0, 2, 1, 2), M(0, 3, 1, 3), M(0, 4, 0, 5)];
    const { detect, cols } = run(rows, merges);
    expect(detect).toEqual({ start: 0, count: 2 });
    expect(cols).toEqual(['사번', '담당자', '거래처ID', '품목', '실적_202212', '실적_202301']);
  });

  it('H4 — 단일 헤더 (병합 없음)', () => {
    const rows: CellValue[][] = [
      ['id', 'name', 'amount', 'created'],
      [1, 'Alice', 100, new Date('2024-01-02')],
      [2, 'Bob', 200, new Date('2024-01-03')],
      [3, 'Carol', 300, new Date('2024-01-04')],
    ];
    const { detect, cols } = run(rows);
    expect(detect).toEqual({ start: 0, count: 1 });
    expect(cols).toEqual(['id', 'name', 'amount', 'created']);
  });

  it('H5 — 제목행 + 단일 헤더 (병합 없음)', () => {
    const rows: CellValue[][] = [
      ['2024년 월간 실적 보고', null, null, null],
      ['사번', '담당자', '품목', '매출'],
      ['MR-01022', '정예준', '가스몬', 55473],
      ['MR-01023', '김철수', '타이레놀', 40094],
    ];
    const { detect, cols } = run(rows);
    expect(detect).toEqual({ start: 1, count: 1 });
    expect(cols).toEqual(['사번', '담당자', '품목', '매출']);
  });

  it('H6 — 제목행 + 2단 헤더 (제목은 트림)', () => {
    const rows: CellValue[][] = [
      ['2024년 월간 실적 보고', null, null, null, null, null],
      ['퍼스널', null, '실적', null, null, null],
      ['사번', '담당자', 202212, 202301, 202302, 202303],
      ['MR-01022', '정예준', 55473, 27101, 29716, 40094],
      ['MR-01023', '김철수', 40404, 66014, 73209, 96755],
    ];
    const merges = [M(0, 0, 0, 5), M(1, 0, 1, 1), M(1, 2, 1, 5)];
    const { detect, cols } = run(rows, merges);
    expect(detect).toEqual({ start: 1, count: 2 });
    expect(cols).toEqual([
      '퍼스널_사번',
      '퍼스널_담당자',
      '실적_202212',
      '실적_202301',
      '실적_202302',
      '실적_202303',
    ]);
  });

  it('H7 — 헤더 없음(첫 행부터 데이터) — 첫 행을 헤더로(허용)', () => {
    const rows: CellValue[][] = [
      ['MR-01022', '정예준', '가스몬', 55473],
      ['MR-01023', '김철수', '타이레놀', 40094],
      ['MR-01024', '이영희', '아스피린', 66014],
    ];
    const { detect } = run(rows);
    expect(detect).toEqual({ start: 0, count: 1 });
  });

  it('H8 — 빈 선두행 + 2단 헤더', () => {
    const rows: CellValue[][] = [
      [null, null, null, null],
      [null, null, null, null],
      ['고객정보', null, '주문정보', null],
      ['고객ID', '이름', '주문ID', '금액'],
      [1, '홍길동', 1001, 5000],
      [2, '김철수', 1002, 7000],
    ];
    const merges = [M(2, 0, 2, 1), M(2, 2, 2, 3)];
    const { detect, cols } = run(rows, merges);
    expect(detect).toEqual({ start: 2, count: 2 });
    expect(cols).toEqual(['고객정보_고객ID', '고객정보_이름', '주문정보_주문ID', '주문정보_금액']);
  });

  it('H9 — 3단(전폭 상위 그룹은 제목처럼 트림)', () => {
    const rows: CellValue[][] = [
      ['실적', null, null, null],
      ['2024', null, '2025', null],
      ['Q1', 'Q2', 'Q1', 'Q2'],
      [100, 200, 300, 400],
      [110, 210, 310, 410],
    ];
    const merges = [M(0, 0, 0, 3), M(1, 0, 1, 1), M(1, 2, 1, 3)];
    const { detect, cols } = run(rows, merges);
    expect(detect).toEqual({ start: 1, count: 2 });
    expect(cols).toEqual(['2024_Q1', '2024_Q2', '2025_Q1', '2025_Q2']);
  });

  it('H10 — 중간 소계 행은 새 헤더가 아님', () => {
    const rows: CellValue[][] = [
      ['사번', '담당자', '매출'],
      ['MR-01022', '정예준', 55473],
      ['MR-01023', '김철수', 40094],
      [null, '소계', 95567],
      ['MR-01024', '이영희', 66014],
    ];
    const { detect, cols } = run(rows);
    expect(detect).toEqual({ start: 0, count: 1 });
    expect(cols).toEqual(['사번', '담당자', '매출']);
  });

  it('H11 — FILE2 + 데이터 영역 세로 병합(카테고리 셀)에 흔들리지 않음', () => {
    const rows: CellValue[][] = [
      ['사번', '담당자', '거래처ID', '품목', '실적', null],
      [null, null, null, null, '202212', '202301'],
      ['MR-01022', '정예준', '강서', '가스몬', 55473, 27101],
      ['MR-01022', '정예준', '서초', '타이레놀', 40094, 40404],
      ['MR-01023', '김철수', '강남', '아스피린', 66014, 73209],
    ];
    const merges = [
      M(0, 0, 1, 0), M(0, 1, 1, 1), M(0, 2, 1, 2), M(0, 3, 1, 3), M(0, 4, 0, 5),
      M(2, 1, 3, 1), // 데이터 영역 세로 병합 (정예준)
    ];
    const { detect, cols } = run(rows, merges);
    expect(detect).toEqual({ start: 0, count: 2 });
    expect(cols).toEqual(['사번', '담당자', '거래처ID', '품목', '실적_202212', '실적_202301']);
  });

  it('H12 — 헤더 아래 배너 병합은 헤더로 오인하지 않음', () => {
    const rows: CellValue[][] = [
      ['이름', '부서', '직급', '입사일'],
      ['홍길동', '영업', '과장', new Date('2020-01-01')],
      ['※ 2024년 기준', null, null, null],
      ['김철수', '개발', '대리', new Date('2021-03-01')],
    ];
    const merges = [M(2, 0, 2, 3)]; // 배너 (데이터 아래) 가로 병합
    const { detect, cols } = run(rows, merges);
    expect(detect).toEqual({ start: 0, count: 1 });
    expect(cols).toEqual(['이름', '부서', '직급', '입사일']);
  });

  it('H13 — 단일 헤더 + 데이터 세로 병합 → legacy 단일 헤더', () => {
    const rows: CellValue[][] = [
      ['지점', '담당', '매출'],
      ['강남', '김', 100],
      ['강남', '이', 200],
      ['서초', '박', 300],
    ];
    const merges = [M(1, 0, 2, 0)]; // 강남 세로 병합 (데이터)
    const { detect, cols } = run(rows, merges);
    expect(detect).toEqual({ start: 0, count: 1 });
    expect(cols).toEqual(['지점', '담당', '매출']);
  });
});
