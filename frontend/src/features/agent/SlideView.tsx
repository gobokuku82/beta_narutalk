/**
 * SlideView — 에이전트 보고서(마크다운)를 채팅창에 슬라이드 카드로 표시 (Phase3, 2026-06-09).
 *
 * 무거운 .pptx 바이너리 대신 "프론트엔드 모양" HTML 시각화 (요구사항: 가볍게, 1 예시).
 * 구조: '# ' = 표지 / '## ' = 섹션 슬라이드. **슬라이드 분할은 여기서, 내용 렌더는 <Markdown>**
 * (근본수정 2026-06-09: 본문을 Markdown 으로 → `**굵게`·`-` 등 마크다운 일관 렌더, 날것 노출 0).
 */
import { Markdown } from '@/components/Markdown';
import { cn } from '@/lib/cn';

export interface Slide {
  title: string;
  /** 슬라이드 본문 (마크다운 — <Markdown> 으로 렌더). */
  body: string;
  cover?: boolean;
}

/** 마크다운 → 슬라이드 배열 (순수 함수). '#'=표지 / '##'=섹션, 이후 줄 = 본문(마크다운 보존). */
export function parseSlides(markdown: string): Slide[] {
  const slides: Slide[] = [];
  let cur: Slide | null = null;

  for (const raw of markdown.split('\n')) {
    const t = raw.trim();
    if (t.startsWith('# ')) {
      cur = { title: t.slice(2).trim(), body: '', cover: true };
      slides.push(cur);
    } else if (t.startsWith('## ')) {
      cur = { title: t.slice(3).trim(), body: '' };
      slides.push(cur);
    } else {
      if (!cur) {
        cur = { title: '개요', body: '' };
        slides.push(cur);
      }
      cur.body += (cur.body ? '\n' : '') + raw;
    }
  }

  return slides.length ? slides : [{ title: '결과', body: markdown.trim() }];
}

export function SlideView({ markdown }: { markdown: string }) {
  const slides = parseSlides(markdown);
  return (
    <div className="mr-8 space-y-2">
      {slides.map((s, i) => (
        <section
          key={i}
          className={cn('rounded-card border border-border bg-card px-4 py-3', s.cover && 'bg-surface-soft')}
        >
          <h3
            className={cn('font-semibold text-foreground', s.cover ? 'text-base' : 'text-sm')}
          >
            {s.title}
          </h3>
          {s.body.trim() && (
            <div className="mt-1">
              <Markdown>{s.body}</Markdown>
            </div>
          )}
          <div className="mt-2 text-2xs tabular-nums text-muted-foreground/50">
            슬라이드 {i + 1} / {slides.length}
          </div>
        </section>
      ))}
    </div>
  );
}
