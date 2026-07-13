/**
 * useDbDesign — DB설계(ERD) 영속 data source.
 *
 * GET /api/db-design/{name}  → 저장된 설계 (없으면 빈 설계)
 * PUT /api/db-design/{name}  → 설계 저장
 * GET /api/db-design          → 저장된 설계 이름 목록
 * 백엔드는 설계 JSON 을 서버측에 영속 (api/routes/db_design.py).
 */
import { rest } from '@/api/rest';
import type { ErdDesign } from '@/features/db_design/store';

export async function fetchDesign(name: string): Promise<ErdDesign> {
  return (await rest.get(`/api/db-design/${encodeURIComponent(name)}`)) as ErdDesign;
}

export async function saveDesign(design: ErdDesign): Promise<ErdDesign> {
  return (await rest.put(
    `/api/db-design/${encodeURIComponent(design.name)}`,
    design,
  )) as ErdDesign;
}

export async function listDesigns(): Promise<{ names: string[] }> {
  return (await rest.get('/api/db-design')) as { names: string[] };
}

// ── 실제 DB 빌드 & 검증 (SQLite) ──────────────────────────────────────────────
export interface BuildTableReport {
  name: string;
  source: 'data' | 'distinct' | 'empty';
  received: number;
  loaded: number;
  dropped_duplicates: number;
}
export interface IntegrityViolation {
  child: string;
  column: string;
  parent: string;
  parent_column: string;
  orphans: number;
  samples: (string | number)[];
}
export interface BuildReport {
  db_path: string;
  order: string[];
  tables: BuildTableReport[];
  integrity: IntegrityViolation[];
}
export interface QueryResult {
  columns: string[];
  rows: (string | number | null)[][];
  truncated: boolean;
}

/** 설계 + 엑셀 추출 행 → SQLite 빌드 + 무결성 리포트. datasets = {테이블명: [{칼럼:값}]}. */
export async function buildDb(
  name: string,
  design: ErdDesign,
  datasets: Record<string, Record<string, unknown>[]>,
): Promise<BuildReport> {
  return (await rest.post(`/api/db-design/${encodeURIComponent(name)}/build`, {
    name: design.name,
    tables: design.tables,
    datasets,
  })) as BuildReport;
}

/** 빌드된 DB 에 SELECT 쿼리(조립 미리보기). */
export async function queryDb(name: string, sql: string, maxRows = 200): Promise<QueryResult> {
  return (await rest.post(`/api/db-design/${encodeURIComponent(name)}/query`, {
    sql,
    max_rows: maxRows,
  })) as QueryResult;
}
