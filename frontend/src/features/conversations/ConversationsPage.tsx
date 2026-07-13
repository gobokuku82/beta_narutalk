/**
 * ConversationsPage — 이전 대화 이력 + 검색 + 클릭→채팅 복원 + 새 대화/삭제.
 *
 * 데이터 (2026-06-10 Phase1 실데이터 배선): GET /api/conversations (checkpoint 기반).
 *  - 목록 = useConversations(client) — ConversationManager가 dreamagent_system checkpoint 조회
 *  - 카드 클릭 → fetchConversationTurns → 채팅창에 복원(메시지 재현)
 *  - + 새 대화 → conversation_id 리셋(session) + 채팅 비우기 + 패널 열기
 *  - 🗑 삭제 → DELETE /api/conversations/{id} (checkpoint 제거, 되돌릴 수 없음)
 */
import { useEffect, useMemo, useState, type MouseEvent } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  History,
  Search,
  MessageSquare,
  CheckCircle2,
  Loader,
  AlertCircle,
  XCircle,
  CircleDashed,
  Plus,
  Trash2,
  type LucideIcon,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { useCurrentClient } from '@/api/clients';
import {
  useConversations,
  fetchConversationTurns,
  deleteConversation,
  type ConversationListItem,
} from '@/api/hooks/useConversations';
import { useAgent } from '@/features/agent/store';
import { turnsToMessages } from '@/features/agent/restore';
import { useChatPanel } from '@/features/agent/chatPanelStore';
import { useSession } from '@/features/session/store';
import { useExecution } from '@/features/execution/store';

const STATUS_META: Record<
  string,
  { label: string; icon: LucideIcon; variant: 'default' | 'secondary' | 'destructive' | 'outline' }
> = {
  active: { label: '진행 중', icon: Loader, variant: 'default' },
  completed: { label: '완료', icon: CheckCircle2, variant: 'secondary' },
  error: { label: '오류', icon: AlertCircle, variant: 'destructive' },
  cancelled: { label: '취소', icon: XCircle, variant: 'outline' },
  incomplete: { label: '미완료', icon: CircleDashed, variant: 'outline' },
};

function fmtDate(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

export function ConversationsPage() {
  const client = useCurrentClient();
  const qc = useQueryClient();
  const { data, isLoading, error } = useConversations(client);
  const [query, setQuery] = useState('');

  // 턴 완료 시 목록 자동 갱신 — 페이지를 보는 동안 새 대화/턴이 실시간 반영.
  const turnCompleted = useExecution((s) => s.isCompleted);
  useEffect(() => {
    if (turnCompleted) qc.invalidateQueries({ queryKey: ['conversations'] });
  }, [turnCompleted, qc]);

  const items = data?.items ?? [];
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (c) =>
        c.title.toLowerCase().includes(q) || c.preview.toLowerCase().includes(q),
    );
  }, [query, items]);

  // 카드 클릭 → 그 대화를 채팅창에 복원(메시지 재현) + 패널 열기.
  const restore = async (item: ConversationListItem) => {
    try {
      const turns = await fetchConversationTurns(item.conversation_id);
      useAgent.getState().loadMessages(turnsToMessages(turns));
      // 복원한 대화를 active 로 — 삭제 시 "열린 대화" 판별 + (P1.5) 이어서 대화 기반.
      useSession.getState().setConversation(item.conversation_id);
      useChatPanel.getState().open();
    } catch (e) {
      console.error('대화 복원 실패', e);
    }
  };

  // + 새 대화 → conversation_id 리셋 + 채팅 비우기 + 패널 열기.
  const startNew = () => {
    useSession.getState().newConversation();
    useAgent.getState().loadMessages([]);
    useChatPanel.getState().open();
  };

  // 🗑 삭제 → 확인 후 checkpoint 제거 → 목록 갱신.
  const remove = async (e: MouseEvent, item: ConversationListItem) => {
    e.stopPropagation();
    if (!window.confirm(`'${item.title}' 대화를 삭제할까요?\n되돌릴 수 없습니다.`)) return;
    try {
      await deleteConversation(item.conversation_id);
      // 지운 대화가 지금 채팅창에 열려있으면 채팅창도 비우기 (새로고침 불필요).
      if (useSession.getState().conversationId === item.conversation_id) {
        useAgent.getState().loadMessages([]);
        useSession.getState().newConversation();
      }
      await qc.invalidateQueries({ queryKey: ['conversations'] });
    } catch (err) {
      console.error('대화 삭제 실패', err);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="대화 이력"
        description="이전 대화 검색 + 다시 이어가기"
        icon={History}
      />

      <div className="flex items-center gap-3">
        <div className="relative max-w-md flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="대화 제목 / 내용 검색..."
            className="pl-9"
          />
        </div>
        <button
          type="button"
          onClick={startNew}
          disabled={!client}
          className="inline-flex shrink-0 items-center gap-2 rounded-button bg-accent-action px-3 py-2 text-sm font-medium text-accent-action-foreground transition-colors hover:bg-accent-action-deep disabled:cursor-not-allowed disabled:opacity-50"
          title="새 대화 시작"
        >
          <Plus className="h-4 w-4" />
          새 대화
        </button>
      </div>

      {!client ? (
        <p className="text-sm text-muted-foreground">상단에서 client를 선택하세요.</p>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">불러오는 중…</p>
      ) : error ? (
        <p className="text-sm text-destructive">대화 이력을 불러오지 못했습니다.</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          아직 대화 이력이 없습니다. ‘새 대화’로 시작하세요.
        </p>
      ) : (
        <div className="space-y-3">
          {filtered.map((c) => {
            const meta = STATUS_META[c.status] ?? STATUS_META.completed!;
            const Icon = meta.icon;
            return (
              <Card
                key={c.conversation_id}
                className="card-hover cursor-pointer"
                onClick={() => restore(c)}
              >
                <CardContent className="flex items-start gap-4 p-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control bg-accent text-accent-foreground">
                    <MessageSquare className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="truncate text-sm font-semibold">{c.title}</p>
                      <Badge variant={meta.variant} className="shrink-0">
                        <Icon className="mr-1 h-3 w-3" />
                        {meta.label}
                      </Badge>
                    </div>
                    <p className="mt-1 truncate text-xs text-muted-foreground">
                      {c.preview}
                    </p>
                    <p className="mt-2 text-2xs text-muted-foreground">
                      {c.turn_count}개 턴 · {fmtDate(c.updated_at)}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => remove(e, c)}
                    className="shrink-0 rounded-full p-2 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                    title="대화 삭제"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </CardContent>
              </Card>
            );
          })}

          {filtered.length === 0 && (
            <p className="text-sm text-muted-foreground">검색 결과가 없습니다.</p>
          )}
        </div>
      )}
    </div>
  );
}
