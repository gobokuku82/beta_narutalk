/**
 * Markdown — 에이전트 출력(마크다운)을 안전하게 렌더 (근본수정, 2026-06-09).
 *
 * react-markdown + remark-gfm. 프론트 디자인 토큰으로 스타일(prose 의존 X) → 대시보드 톤 일치.
 * SlideView(슬라이드 내용) + 텍스트 말풍선 공유 → `**굵게**`·`#`·`-` 날것 노출을 한 곳에서 근본 제거.
 * (react-markdown 은 dangerouslySetInnerHTML 안 씀 — React 요소 생성, XSS 안전.)
 */
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
// CJK 친화 emphasis: '**굵게**로'(닫는 ** 뒤 한글)도 굵게 파싱 (CommonMark flanking 한계 보정).
import remarkCjkFriendly from 'remark-cjk-friendly';

const components: Components = {
  h1: ({ children }) => <h3 className="mb-1 mt-2 text-base font-semibold font-display text-foreground">{children}</h3>,
  h2: ({ children }) => <h4 className="mb-1 mt-2 text-sm font-semibold font-display text-foreground">{children}</h4>,
  h3: ({ children }) => <h5 className="mb-1 mt-2 text-sm font-semibold font-display text-foreground">{children}</h5>,
  p: ({ children }) => <p className="my-1 text-sm leading-relaxed text-foreground/90">{children}</p>,
  ul: ({ children }) => (
    <ul className="my-1 list-disc space-y-1 pl-5 text-sm text-foreground/90 marker:text-muted-foreground/60">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="my-1 list-decimal space-y-1 pl-5 text-sm text-foreground/90">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noreferrer" className="text-accent-action-deep underline underline-offset-2">
      {children}
    </a>
  ),
  code: ({ children }) => <code className="rounded-sm bg-muted px-1 py-1 text-xs">{children}</code>,
  table: ({ children }) => (
    <div className="my-2 overflow-x-auto">
      <table className="w-full border-collapse text-xs">{children}</table>
    </div>
  ),
  th: ({ children }) => <th className="border border-border px-2 py-1 text-left font-medium">{children}</th>,
  td: ({ children }) => <td className="border border-border px-2 py-1">{children}</td>,
};

export function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm, remarkCjkFriendly]} components={components}>
      {children}
    </ReactMarkdown>
  );
}
