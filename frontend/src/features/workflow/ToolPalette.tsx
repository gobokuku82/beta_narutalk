/**
 * ToolPalette — workflow 페이지 좌측 도킹.
 *
 * 프레임 추출 후 도구 카탈로그는 비어 있음(도메인별 도구는 런타임 등록).
 * 빈 팔레트 placeholder — 워크플로우 캔버스 authoring UX 유지. (2026-06-19)
 */
import { useState } from 'react';
import { Search } from 'lucide-react';

export function ToolPalette() {
  const [search, setSearch] = useState('');

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="px-3 py-2 border-b border-border flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wide">Tool Palette</h3>
        </div>
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="이름·설명 검색"
            className="w-full h-7 pl-7 pr-2 text-2xs rounded-sm border border-input bg-background focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <p className="px-3 py-6 text-2xs text-center text-muted-foreground">
          등록된 도구가 없습니다.
          <br />
          도메인 도구는 런타임에 등록됩니다.
        </p>
      </div>
    </div>
  );
}
