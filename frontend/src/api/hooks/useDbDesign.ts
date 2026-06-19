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
