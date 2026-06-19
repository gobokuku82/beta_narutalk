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

  const [ddl, setDdl] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string>('');

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
          <Button size="sm" variant="outline" className="h-7 text-2xs" onClick={addTable}>
            + 테이블
          </Button>
          <Button size="sm" variant="outline" className="h-7 text-2xs" onClick={onGenerateDdl}>
            DDL 출력
          </Button>
          <Button size="sm" className="h-7 text-2xs" onClick={onSave} disabled={saving}>
            {saving ? '저장 중…' : '저장'}
          </Button>
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
          <div className="flex items-center gap-2 border-b border-border px-4 py-1.5">
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
    </div>
  );
}
