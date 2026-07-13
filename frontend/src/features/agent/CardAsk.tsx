/**
 * CardAsk — 카드 hover ✨ → 액션 팝업 → 에이전트 연결 (P2+P3).
 *
 * 카드(결과 표시)를 감싸면 hover 시 우상단 ✨ 페이드인 → 클릭 → 액션 메뉴.
 * 상단 컨텍스트 칩 = 카드 데이터(항목·값·기간·출처) — 에이전트에 넘기는 것과 동일(투명성).
 * 라우팅 = 문구 유도(P3, 백엔드 0) — 검증된 표현 사용:
 *   진단 "왜 …인지 원인 분석" → diagnose / 추천 "개선안 추천" → recommend /
 *   재검증 "재계산해서 …맞는지 검증" → measure.
 * 🔍 숫자나온방법·⚡ 해줘(MVP)는 비활성 정직 표시.
 */
import { useState, type ReactNode } from 'react';
import {
  BarChart3,
  CheckCheck,
  Lightbulb,
  MessageSquare,
  Search,
  Zap,
} from 'lucide-react';
import { toast } from 'sonner';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useCurrentClient } from '@/api/clients';
import { useChatPanel } from './chatPanelStore';
import { askAgent, type AskAgentResult, type CardContext } from './actions';

const FAIL_MESSAGE: Record<Exclude<AskAgentResult, { ok: true }>['reason'], string> = {
  not_connected: '서버에 연결되어 있지 않습니다. 잠시 후 다시 시도하세요.',
  busy: '에이전트가 작업 중입니다. 완료 후 다시 시도하세요.',
  send_failed: '송신에 실패했습니다. 연결 상태를 확인하세요.',
};
// (2026-07-02) no_client 사유 폐지 — workspace(구 client) 미해석 시에도 generic 모드로 전송.

interface Props {
  context: CardContext;
  /** 데이터 로딩 중이면 ✨ 숨김 (값 '-' 로 질문하는 것 방지) */
  disabled?: boolean;
  children: ReactNode;
}

/** 카드 1장을 감싸 ✨ 액션 메뉴를 부착. */
export function CardAsk({ context, disabled, children }: Props) {
  const client = useCurrentClient();
  const [open, setOpen] = useState(false);

  const ask = (prompt: string) => {
    const r = askAgent({ prompt, client, context });
    if (!r.ok) toast.warning(FAIL_MESSAGE[r.reason]);
  };

  const { metric, value, period } = context;

  return (
    <div className="group relative">
      {children}
      {!disabled && (
        <DropdownMenu open={open} onOpenChange={setOpen}>
          <DropdownMenuTrigger asChild>
            {/* 항상 보이는 '에이전트' 필 — hover 전용은 발견 불가(2026-06-12 확정).
                카드 모서리 플로팅 = 카드 자체 아이콘(우상단)·tooltip ⓘ(우하단)와 충돌 회피.
                채운 accent-action(코발트) 1색·플랫, 아이콘 없음 (그라데이션/glow 금지 — 디자인시스템 원칙). */}
            <button
              type="button"
              aria-label={`${metric} — 에이전트에게 물어보기`}
              title="에이전트에게 물어보기"
              className={`absolute -right-2 -top-2 z-10 rounded-full px-2 py-1 text-xs font-medium transition-colors duration-150 ${
                open
                  ? 'bg-accent-action text-accent-action-foreground'
                  : 'bg-accent-action/10 text-accent-action hover:bg-accent-action hover:text-accent-action-foreground'
              }`}
            >
              에이전트
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-72">
            {/* 컨텍스트 칩 — 무엇을 묻는지 = 신뢰 (§2.1) */}
            <DropdownMenuLabel>
              <div className="text-sm">
                {metric} <span className="font-bold">{value}</span>
              </div>
              <div className="mt-1 text-xs font-normal text-muted-foreground">
                {period}
                {context.methodology ? ` · ${context.methodology}` : ''}
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />

            <DropdownMenuItem
              onClick={() => ask(`${period} ${metric}이(가) ${value}인데 왜 이런지 원인 분석해줘`)}
            >
              <BarChart3 className="mr-2 h-4 w-4" />
              왜 이런지 분석 (진단)
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => ask(`${metric} ${value}의 개선안을 추천해줘`)}>
              <Lightbulb className="mr-2 h-4 w-4" />
              개선안 추천
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => ask(`${period} ${metric}을 재계산해서 ${value}이 맞는지 검증해줘`)}
            >
              <CheckCheck className="mr-2 h-4 w-4" />
              재검증 (재계산 확인)
            </DropdownMenuItem>

            <DropdownMenuSeparator />
            <DropdownMenuItem disabled>
              <Search className="mr-2 h-4 w-4" />
              숫자 나온 방법 <span className="ml-auto text-xs">(예정)</span>
            </DropdownMenuItem>
            <DropdownMenuItem disabled>
              <Zap className="mr-2 h-4 w-4" />
              해줘 <span className="ml-auto text-xs">(MVP)</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => useChatPanel.getState().open()}>
              <MessageSquare className="mr-2 h-4 w-4" />
              직접 묻기
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  );
}
