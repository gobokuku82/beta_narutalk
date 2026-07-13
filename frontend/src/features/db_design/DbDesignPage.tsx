/**
 * DbDesignPage — 시스템 → DB설계.
 *
 * 테이블/컬럼 생성·연결(ERD) + DDL(PostgreSQL) 출력 + 백엔드 영속(저장/복원).
 * 좌: ERD 캔버스 / 우: 선택 테이블 편집 패널 / 상단: 툴바 / 하단(토글): DDL 출력.
 * (v1: DDL 출력만 — 실제 DB 적용 없음.)
 */
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { ErdCanvas } from './ErdCanvas';
import { TablePanel } from './TablePanel';
import { ExcelImportDialog } from './ExcelImportDialog';
import { DimensionHelperDialog } from './DimensionHelperDialog';
import { DbBuildDialog } from './DbBuildDialog';
import { MetricDiscoveryDialog } from './MetricDiscoveryDialog';
import { generateDDL } from './ddl';
import { useDbDesign } from './store';
import { fetchDesign, saveDesign } from '@/api/hooks/useDbDesign';

export function DbDesignPage() {
  const name = useDbDesign((s) => s.name);
  const dirty = useDbDesign((s) => s.dirty);
  const tableCount = useDbDesign((s) => s.tables.length);
  const addTable = useDbDesign((s) => s.addTable);
  const load = useDbDesign((s) => s.load);
  const serialize = useDbDesign((s) => s.serialize);
  const markSaved = useDbDesign((s) => s.markSaved);
  const clearAll = useDbDesign((s) => s.clearAll);

  const [ddl, setDdl] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string>('');
  const [importOpen, setImportOpen] = useState(false);
  const [dimOpen, setDimOpen] = useState(false);
  const [buildOpen, setBuildOpen] = useState(false);
  const [metricOpen, setMetricOpen] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);

  // 진입 시 저장된 설계 복원 (없으면 빈 설계 유지)
  useEffect(() => {
    let alive = true;
    fetchDesign(name)
      .then((d) => {
        if (alive && d && Array.isArray(d.tables)) load(d);
      })
      .catch(() => {
        /* 없음 — 빈 설계로 시작 */
      });
    return () => {
      alive = false;
    };
    // name 은 초기 고정 — 1회 로드
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSave = async () => {
    setSaving(true);
    setStatus('');
    try {
      await saveDesign(serialize());
      markSaved();
      setStatus('저장됨');
    } catch (e) {
      setStatus(`저장 실패: ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  const onGenerateDdl = () => setDdl(generateDDL(serialize()));

  const onCopyDdl = async () => {
    if (ddl) {
      try {
        await navigator.clipboard.writeText(ddl);
        setStatus('DDL 복사됨');
      } catch {
        setStatus('복사 실패 (수동 선택)');
      }
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* 툴바 */}
      <header className="flex items-center gap-2 border-b border-border px-4 py-2">
        <h1 className="text-sm font-semibold">DB설계</h1>
        <span className="font-mono text-2xs text-muted-foreground">
          {name} · {tableCount} tables{dirty ? ' · 변경됨' : ''}
        </span>
        <div className="ml-auto flex items-center gap-2">
          {status && <span className="text-2xs text-muted-foreground">{status}</span>}
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-2xs"
            onClick={() => setImportOpen(true)}
          >
            엑셀 가져오기
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-2xs"
            onClick={() => setDimOpen(true)}
            disabled={tableCount === 0}
            title="실적(팩트)의 키 칼럼을 마스터(차원) 테이블로 분리 + FK"
          >
            차원 추출
          </Button>
          <Button size="sm" variant="outline" className="h-7 text-2xs" onClick={addTable}>
            + 테이블
          </Button>
          <Button size="sm" variant="outline" className="h-7 text-2xs" onClick={onGenerateDdl}>
            DDL 출력
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-2xs"
            onClick={() => setBuildOpen(true)}
            disabled={tableCount === 0}
            title="설계대로 실제 SQLite 를 빌드 + 데이터 적재 + 무결성 검사 + JOIN 미리보기"
          >
            DB 빌드
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-2xs"
            onClick={() => setMetricOpen(true)}
            disabled={tableCount === 0}
            title="데이터 모양에서 후보 지표 자동 제안 → SQL 초안 → 빌드 DB에 실행"
          >
            지표 발견
          </Button>
          <Button size="sm" className="h-7 text-2xs" onClick={onSave} disabled={saving}>
            {saving ? '저장 중…' : '저장'}
          </Button>
          <span className="mx-1 h-5 w-px bg-border" />
          {confirmClear ? (
            <span className="flex items-center gap-1">
              <span className="text-2xs text-muted-foreground">{tableCount}개 모두 삭제?</span>
              <Button
                size="sm"
                variant="destructive"
                className="h-7 text-2xs"
                onClick={() => {
                  clearAll();
                  setConfirmClear(false);
                  setStatus('모든 테이블 삭제됨 · 저장하면 반영');
                }}
              >
                확인
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-2xs"
                onClick={() => setConfirmClear(false)}
              >
                취소
              </Button>
            </span>
          ) : (
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-2xs text-muted-foreground hover:text-destructive"
              onClick={() => setConfirmClear(true)}
              disabled={tableCount === 0}
              title="현재 캔버스의 모든 테이블 삭제 (설계명 유지 · 저장해야 영속)"
            >
              모두 삭제
            </Button>
          )}
        </div>
      </header>

      {/* 본문: 캔버스 + 편집 패널 */}
      <div className="flex min-h-0 flex-1">
        <div className="min-w-0 flex-1">
          <ErdCanvas />
        </div>
        <aside className="w-72 shrink-0 border-l border-border">
          <TablePanel />
        </aside>
      </div>

      {/* DDL 출력 (토글) */}
      {ddl !== null && (
        <div className="flex max-h-[40%] flex-col border-t border-border bg-card">
          <div className="flex items-center gap-2 border-b border-border px-4 py-2">
            <span className="text-2xs font-semibold uppercase tracking-wide text-muted-foreground">
              DDL (PostgreSQL)
            </span>
            <div className="ml-auto flex gap-2">
              <Button size="sm" variant="outline" className="h-6 text-2xs" onClick={onCopyDdl}>
                복사
              </Button>
              <Button size="sm" variant="ghost" className="h-6 text-2xs" onClick={() => setDdl(null)}>
                닫기
              </Button>
            </div>
          </div>
          <textarea
            readOnly
            value={ddl}
            className="flex-1 resize-none bg-background p-3 font-mono text-2xs text-foreground focus:outline-none"
            spellCheck={false}
          />
        </div>
      )}

      <ExcelImportDialog open={importOpen} onOpenChange={setImportOpen} />
      <DimensionHelperDialog open={dimOpen} onOpenChange={setDimOpen} />
      <DbBuildDialog open={buildOpen} onOpenChange={setBuildOpen} />
      <MetricDiscoveryDialog open={metricOpen} onOpenChange={setMetricOpen} />
    </div>
  );
}
