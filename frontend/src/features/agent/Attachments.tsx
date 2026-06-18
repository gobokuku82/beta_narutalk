/**
 * Attachments — 어시스턴트 응답의 다운로드 산출물(pdf/ppt 등)을 작은 칩으로 (Phase3 다운로드, 2026-06-09).
 *
 * 백엔드 ResponsePayload.attachments[] → store.ChatAttachment(url 보유분) → 여기서 다운로드 링크.
 * url 은 상대경로(/api/files/download?p=...) — BASE_URL 붙여 절대 URL. 엔드포인트가 filename 헤더 부여 → 클릭=다운로드.
 * 디자인: 중립 아웃라인 칩(그라데이션/glow 금지, 액센트 0 — 제품 톤).
 */
import { Download } from 'lucide-react';
import { BASE_URL } from '@/api/rest';
import type { ChatAttachment } from './store';

const KIND_LABEL: Record<string, string> = {
  pdf: 'PDF',
  ppt: 'PPT',
  pptx: 'PPT',
  excel: 'Excel',
  xlsx: 'Excel',
  word: 'Word',
  chart: '차트',
  image: '이미지',
  link: '링크',
};

function label(kind: string): string {
  return KIND_LABEL[kind.toLowerCase()] ?? kind.toUpperCase();
}

export function Attachments({ items }: { items?: ChatAttachment[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="mr-8 mt-1 flex flex-wrap gap-2">
      {items.map((a, i) => (
        <a
          key={`${a.url}-${i}`}
          href={`${BASE_URL}${a.url}`}
          download
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2 py-1 text-xs font-medium text-foreground/80 transition-colors hover:bg-muted hover:text-foreground"
          title={a.caption ?? `${label(a.kind)} 다운로드`}
        >
          <Download className="h-3.5 w-3.5 text-muted-foreground" />
          {label(a.kind)}
        </a>
      ))}
    </div>
  );
}
