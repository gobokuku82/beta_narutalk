/**
 * DimensionHelperDialog — 차원 추출 도우미.
 *
 * 팩트(실적) 테이블의 "키 칼럼"을 훑어 → 마스터(차원) 테이블로 분리/연결을 *제안*하고,
 * 고른 항목을 일괄 적용(테이블 생성 + FK). = 정규화 자동화의 가이드형 진입점.
 * 탐지 = dimensions.suggestDimensions(이름 휴리스틱). 적용 = store.applyDimensionSuggestions.
 * 이름만으로 안 잡히는 키(사번·품목 등)는 우측 패널의 칼럼별 "차원 추출"로.
 */
import { useMemo, useState } from 'react';
import { toast } from 'sonner';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/cn';
import { useDbDesign } from './store';
import { suggestDimensions, type DimensionSuggestion } from './dimensions';

interface RowState {
  include: boolean;
  masterName: string;
}

export function DimensionHelperDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const tables = useDbDesign((s) => s.tables);
  const applySuggestions = useDbDesign((s) => s.applyDimensionSuggestions);

  // 다이얼로그가 열린 동안의 제안 스냅샷 (열릴 때 고정 — 적용 전까지 안정적 id).
  const suggestions = useMemo(
    () => (open ? suggestDimensions(tables) : []),
    // open 토글 시에만 재계산 (tables 변화로 중간에 흔들리지 않게)
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [open],
  );

  const [rows, setRows] = useState<Record<string, RowState>>({});
  const stateFor = (s: DimensionSuggestion): RowState =>
    rows[s.key] ?? { include: true, masterName: s.masterName };

  const patch = (key: string, p: Partial<RowState>) =>
    setRows((r) => ({ ...r, [key]: { ...(r[key] ?? { include: true, masterName: '' }), ...p } }));

  const selected = suggestions.filter((s) => stateFor(s).include);

  const onApply = () => {
    const payload: DimensionSuggestion[] = selected.map((s) => ({
      ...s,
      masterName: stateFor(s).masterName.trim() || s.masterName,
    }));
    if (payload.length === 0) {
      toast.error('적용할 항목을 선택하세요');
      return;
    }
    const created = applySuggestions(payload);
    const linked = payload.length - created;
    toast.success(
      `차원 ${payload.length}건 적용 · 생성 ${created}개${linked ? ` · 연결 ${linked}건` : ''}`,
    );
    setRows({});
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[80vh] max-w-2xl flex-col">
        <DialogHeader>
          <DialogTitle>차원 추출 도우미</DialogTitle>
          <DialogDescription>
            실적(팩트)의 키 칼럼을 마스터(차원) 테이블로 분리하고 FK 로 잇습니다. 키 이름은
            <span className="font-mono"> 거래처ID·품목코드</span> 처럼 추정하며, 기존 마스터가 있으면
            연결만 합니다. 이름만으로 안 잡히는 키는 우측 패널에서 칼럼별로 추출하세요.
          </DialogDescription>
        </DialogHeader>

        {suggestions.length === 0 ? (
          <div className="rounded-input border border-dashed border-border px-4 py-8 text-center text-2xs text-muted-foreground">
            분리할 만한 키 칼럼을 찾지 못했어요.
            <br />
            우측 패널에서 칼럼의 <span className="font-mono">⇲ 차원</span> 버튼으로 직접 추출할 수
            있습니다.
          </div>
        ) : (
          <ul className="flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto pr-1">
            {suggestions.map((s) => {
              const st = stateFor(s);
              const isCreate = s.existing === null;
              const where =
                s.sources[0]?.tableName +
                (s.sources.length > 1 ? ` 외 ${s.sources.length - 1}곳` : '');
              return (
                <li
                  key={s.key}
                  className={cn(
                    'flex items-center gap-2 rounded-input border p-2 text-2xs',
                    st.include ? 'border-border bg-card' : 'border-border/60 bg-muted/30 opacity-70',
                  )}
                >
                  <input
                    type="checkbox"
                    checked={st.include}
                    onChange={(e) => patch(s.key, { include: e.target.checked })}
                    className="h-3.5 w-3.5 accent-accent-action"
                  />
                  <span
                    className={cn(
                      'shrink-0 rounded-sm border px-1.5 py-0.5 font-mono',
                      isCreate
                        ? 'border-accent-action/40 bg-accent-action/10 text-accent-action'
                        : 'border-border text-muted-foreground',
                    )}
                    title={isCreate ? '새 마스터 테이블 생성' : '기존 마스터에 연결만'}
                  >
                    {isCreate ? '생성' : '연결'}
                  </span>
                  <span className="font-mono text-muted-foreground">{where}.</span>
                  <span className="font-medium">{s.key}</span>
                  <span className="text-muted-foreground">→</span>
                  {isCreate ? (
                    <Input
                      value={st.masterName}
                      onChange={(e) => patch(s.key, { masterName: e.target.value })}
                      className="h-6 max-w-[160px] text-2xs"
                      title="만들 마스터 테이블명"
                    />
                  ) : (
                    <span className="font-medium text-accent-action">{s.masterName}</span>
                  )}
                </li>
              );
            })}
          </ul>
        )}

        <div className="flex items-center gap-2 border-t border-border pt-3">
          <span className="text-2xs text-muted-foreground">
            마스터엔 <span className="font-mono">PK</span> + <span className="font-mono">이름</span>{' '}
            칼럼 자리만 만듭니다. 실제 값 적재는 다운스트림(SQL).
          </span>
          <div className="ml-auto flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="h-8 text-2xs"
              onClick={() => onOpenChange(false)}
            >
              취소
            </Button>
            <Button
              size="sm"
              className="h-8 text-2xs"
              disabled={selected.length === 0}
              onClick={onApply}
            >
              추출{selected.length > 0 ? ` (${selected.length}건)` : ''}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
