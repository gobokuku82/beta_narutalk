/**
 * 지표 발견기 — 데이터 모양(ERD)에서 후보 지표를 *규칙으로 자동 제안*.
 *
 * 컨셉(overview §4.2): "어떤 지표가 필요한지 모름"이 정상 → 빈 폼에서 발명하지 말고
 * 팩트(측정값+차원+시간)의 모양에서 후보를 뽑아 사용자가 *고르고 다듬게* 한다.
 * 각 지표에 SQL 초안(metricToSql)을 붙여 빌드된 SQLite 에 바로 돌려볼 수 있다(루프 닫힘).
 * 순수 함수 — UI 비의존, 테스트 가능. (auto-FK / 차원 추출과 동일 철학.)
 */
import type { ErdTable, ErdColumn } from './store';

export type Aggregate = 'SUM' | 'COUNT' | 'AVG' | 'MIN' | 'MAX' | 'COUNT_DISTINCT';
export type ChartKind = 'kpi' | 'line' | 'bar' | 'pie' | 'table';
/** 발견 카테고리 — 그룹/라벨용. */
export type MetricKind = 'kpi' | 'trend' | 'breakdown' | 'trend_by' | 'growth';

export interface MetricDimension {
  column: string;
  time: boolean; // 시간 축이면 true
}

export interface Metric {
  id: string;
  name: string;
  kind: MetricKind;
  sourceTable: string;
  aggregate: Aggregate;
  measure: string | null; // null = COUNT(*)
  dimensions: MetricDimension[];
  chart: ChartKind;
  sort: 'asc' | 'desc' | null;
  limit: number | null;
}

const NUMERIC = /^(INTEGER|BIGINT|SMALLINT|INT|NUMERIC|FLOAT|REAL|DOUBLE|DECIMAL)/i;
const DATE_TYPE = /^(DATE|TIMESTAMP)/i;
// 시간 축 — 정확히. 이름 전체가 시간이거나(월·년월…), 안전한 부분일치(년월·연월·분기)만.
// '월방문횟수'·'월평균사용예산'(측정값)이 '월' 부분일치로 시간 축이 되던 오탐 방지.
const TIME_EXACT = /^(년월|연월|월|기간|날짜|일자|분기|ym|date|month|period|yearmonth)$/i;
const TIME_SUB = /(년월|연월|분기)/;

function isNumeric(c: ErdColumn): boolean {
  return NUMERIC.test(c.type || '');
}
function isTime(c: ErdColumn): boolean {
  const n = c.name.trim();
  return DATE_TYPE.test(c.type || '') || TIME_EXACT.test(n) || TIME_SUB.test(n);
}

/** 팩트 1개의 칼럼을 측정값/시간/차원으로 분류. */
interface FactShape {
  measures: ErdColumn[];
  time: ErdColumn | null;
  dims: ErdColumn[]; // FK + 범주형(비측정·비시간·비PK)
}
function classify(t: ErdTable): FactShape {
  const measures: ErdColumn[] = [];
  const dims: ErdColumn[] = [];
  let time: ErdColumn | null = null;
  for (const c of t.columns) {
    if (isTime(c)) {
      if (!time) time = c;
      else dims.push(c); // 두 번째 시간성 칼럼은 차원 취급
      continue;
    }
    if (c.pk) {
      // 단일 PK 는 차원으로 부적합(레코드 식별자) — 건너뜀. 복합키 일부는 차원.
      const pkCount = t.columns.filter((x) => x.pk).length;
      if (pkCount > 1) dims.push(c);
      continue;
    }
    if (isNumeric(c) && !c.fk) measures.push(c);
    else dims.push(c); // FK + 텍스트 범주
  }
  return { measures, time, dims };
}

/** 팩트 후보 = 측정값이 하나라도 있고 (시간 또는 차원이 있는) 테이블. */
export function isFactTable(t: ErdTable): boolean {
  const { measures, time, dims } = classify(t);
  return measures.length > 0 && (time !== null || dims.length > 0);
}

function slug(s: string): string {
  return s.replace(/[^A-Za-z0-9가-힣]+/g, '').slice(0, 24);
}

/**
 * 후보 지표 제안. 각 팩트 × 측정값에 대해:
 *  KPI(총합) · 시간추이(line) · 차원별 Top-N(bar) · 차원×시간 추이(line) · 전월대비 성장(bar).
 * id 는 결정적(테이블·종류·측정·차원 슬러그) — 테스트/중복제거 안정.
 */
export function suggestMetrics(tables: ErdTable[]): Metric[] {
  const out: Metric[] = [];
  for (const t of tables) {
    const { measures, time, dims } = classify(t);
    if (measures.length === 0 || (time === null && dims.length === 0)) continue;
    const fkDims = dims.filter((d) => d.fk);
    const breakdownDims = dims.length ? dims : fkDims;

    for (const m of measures) {
      const M = m.name;
      const base = { sourceTable: t.name, aggregate: 'SUM' as Aggregate, measure: M };

      // 1) KPI — 총합
      out.push({
        ...base,
        id: `${slug(t.name)}_kpi_${slug(M)}`,
        kind: 'kpi',
        name: `총 ${M}`,
        dimensions: [],
        chart: 'kpi',
        sort: null,
        limit: null,
      });

      // 2) 시간 추이
      if (time) {
        out.push({
          ...base,
          id: `${slug(t.name)}_trend_${slug(M)}`,
          kind: 'trend',
          name: `${M} ${time.name}별 추이`,
          dimensions: [{ column: time.name, time: true }],
          chart: 'line',
          sort: 'asc',
          limit: null,
        });
        // 5) 전월대비 성장
        out.push({
          ...base,
          id: `${slug(t.name)}_growth_${slug(M)}`,
          kind: 'growth',
          name: `${M} 전기간대비 성장`,
          dimensions: [{ column: time.name, time: true }],
          chart: 'bar',
          sort: 'asc',
          limit: null,
        });
      }

      // 3) 차원별 Top-N
      for (const d of breakdownDims) {
        out.push({
          ...base,
          id: `${slug(t.name)}_bd_${slug(M)}_${slug(d.name)}`,
          kind: 'breakdown',
          name: `${d.name}별 ${M} Top10`,
          dimensions: [{ column: d.name, time: false }],
          chart: 'bar',
          sort: 'desc',
          limit: 10,
        });
      }

      // 4) 차원 × 시간 추이 (FK 차원만 — 다계열)
      if (time) {
        for (const d of fkDims) {
          out.push({
            ...base,
            id: `${slug(t.name)}_tb_${slug(M)}_${slug(d.name)}`,
            kind: 'trend_by',
            name: `${d.name}별 ${M} ${time.name} 추이`,
            dimensions: [
              { column: d.name, time: false },
              { column: time.name, time: true },
            ],
            chart: 'line',
            sort: 'asc',
            limit: null,
          });
        }
      }
    }
  }
  return out;
}

function q(id: string): string {
  return '"' + String(id).replace(/"/g, '""') + '"';
}

/**
 * 지표 → SQL 초안 (SQLite/Postgres 공통: 식별자 큰따옴표). 빌드된 DB 에 바로 실행 가능.
 * growth 는 윈도우 함수(LAG)로 전기간 대비 증감을 계산.
 */
export function metricToSql(m: Metric): string {
  const fact = q(m.sourceTable);
  const valueAlias = q(m.measure ? `${m.aggregate.toLowerCase()}_${m.measure}` : 'count');
  const agg = m.measure ? `${m.aggregate}(${q(m.measure)})` : 'COUNT(*)';

  if (m.kind === 'kpi') {
    return `SELECT ${agg} AS ${valueAlias}\nFROM ${fact}`;
  }

  const dimCols = m.dimensions.map((d) => q(d.column));
  const groupBy = dimCols.join(', ');

  if (m.kind === 'growth') {
    const tcol = q(m.dimensions[0]?.column ?? '기간');
    const val = q(`${m.aggregate.toLowerCase()}_${m.measure}`);
    return (
      `SELECT ${tcol}, ${agg} AS ${val},\n` +
      `  ${agg} - LAG(${agg}) OVER (ORDER BY ${tcol}) AS ${q('전기간대비')}\n` +
      `FROM ${fact}\nGROUP BY ${tcol}\nORDER BY ${tcol}`
    );
  }

  let sql = `SELECT ${groupBy}, ${agg} AS ${valueAlias}\nFROM ${fact}\nGROUP BY ${groupBy}`;
  if (m.sort) {
    const orderCol = m.kind === 'breakdown' ? valueAlias : (dimCols[dimCols.length - 1] ?? valueAlias);
    sql += `\nORDER BY ${orderCol} ${m.sort.toUpperCase()}`;
  }
  if (m.limit) sql += `\nLIMIT ${m.limit}`;
  return sql;
}
