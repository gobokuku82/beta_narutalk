/**
 * SettingsPage — 테마 / 계정 / 알림 / 토큰 사용량.
 *
 * Sprint 3 (화면설계 + mock 구동). 테마는 실제 동작 (useSettings),
 * 계정 / 알림 / 토큰은 화면설계 + 로컬 상태 (백엔드 연동 Sprint 6+).
 */
import { useState } from 'react';
import {
  Settings as SettingsIcon,
  Sun,
  Moon,
  Monitor,
  User,
  Bell,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useSettings, type Theme } from './store';
import { cn } from '@/lib/cn';

const THEMES: Array<{ value: Theme; label: string; icon: LucideIcon }> = [
  { value: 'light', label: '라이트', icon: Sun },
  { value: 'dark', label: '다크', icon: Moon },
  { value: 'system', label: '시스템', icon: Monitor },
];

const NOTIFICATION_OPTIONS = [
  { key: 'hitl', label: '승인 요청 알림', desc: 'AI 가 검토를 요청할 때 알림' },
  { key: 'report', label: '리포트 생성 완료', desc: '리포트 생성이 끝나면 알림' },
  { key: 'fatigue', label: '소재 피로도 경고', desc: '피로 소재 발생 시 알림' },
] as const;

function Toggle({ on, onClick }: { on: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'relative h-6 w-11 shrink-0 rounded-full transition-colors',
        on ? 'bg-primary' : 'bg-muted',
      )}
    >
      <span
        className={cn(
          'absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform',
          on ? 'translate-x-[22px]' : 'translate-x-0.5',
        )}
      />
    </button>
  );
}

export function SettingsPage() {
  const theme = useSettings((s) => s.theme);
  const setTheme = useSettings((s) => s.setTheme);
  const [notifications, setNotifications] = useState<Record<string, boolean>>({
    hitl: true,
    report: true,
    fatigue: false,
  });

  // mock 토큰 사용량
  const tokenUsed = 142_500;
  const tokenLimit = 500_000;
  const tokenPct = Math.round((tokenUsed / tokenLimit) * 100);

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="설정"
        description="테마 / 계정 / 알림 / 토큰 사용량"
        icon={SettingsIcon}
      />

      <div className="mx-auto max-w-3xl space-y-6">
        {/* 테마 */}
        <Card>
          <CardHeader>
            <CardTitle>테마</CardTitle>
            <CardDescription>화면 색상 모드 — 즉시 적용됩니다.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-3">
              {THEMES.map((t) => {
                const Icon = t.icon;
                const active = theme === t.value;
                return (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => setTheme(t.value)}
                    className={cn(
                      'flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-all',
                      active
                        ? 'border-primary bg-accent'
                        : 'border-border hover:border-primary/40',
                    )}
                  >
                    <Icon
                      className={cn(
                        'h-6 w-6',
                        active ? 'text-primary' : 'text-muted-foreground',
                      )}
                    />
                    <span
                      className={cn(
                        'text-sm font-medium',
                        active && 'text-primary',
                      )}
                    >
                      {t.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* 계정 */}
        <Card>
          <CardHeader>
            <CardTitle>계정</CardTitle>
            <CardDescription>로그인 정보</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="bg-primary flex h-14 w-14 items-center justify-center rounded-xl text-xl font-bold text-primary-foreground">
                <User className="h-7 w-7" />
              </div>
              <div>
                <p className="text-sm font-bold">OctorAD 사용자</p>
                <p className="text-xs text-muted-foreground">marketing@octorad.ai</p>
                <span className="mt-1 inline-block rounded-sm bg-accent px-2 py-1 text-2xs font-medium text-accent-foreground">
                  Marketing Manager
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 알림 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-4 w-4" />
              알림
            </CardTitle>
            <CardDescription>받을 알림 유형을 선택하세요.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {NOTIFICATION_OPTIONS.map((opt) => (
                <div
                  key={opt.key}
                  className="flex items-center justify-between rounded-lg border border-border p-3"
                >
                  <div>
                    <p className="text-sm font-medium">{opt.label}</p>
                    <p className="text-xs text-muted-foreground">{opt.desc}</p>
                  </div>
                  <Toggle
                    on={!!notifications[opt.key]}
                    onClick={() =>
                      setNotifications((n) => ({ ...n, [opt.key]: !n[opt.key] }))
                    }
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 토큰 사용량 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              토큰 사용량
            </CardTitle>
            <CardDescription>이번 달 LLM 토큰 사용 현황 (mock)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between">
              <p className="text-2xl font-bold tabular-nums">
                {tokenUsed.toLocaleString('ko-KR')}
              </p>
              <p className="text-sm text-muted-foreground">
                / {tokenLimit.toLocaleString('ko-KR')} 토큰
              </p>
            </div>
            <div className="mt-2 h-3 overflow-hidden rounded-full bg-muted">
              <div
                className="bg-primary h-full rounded-full transition-all"
                style={{ width: `${tokenPct}%` }}
              />
            </div>
            <p className="mt-1.5 text-xs text-muted-foreground">
              {tokenPct}% 사용 — 다음 갱신: 2026-06-01
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
