// @vitest-environment jsdom
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Markdown } from './Markdown';

describe('Markdown — 마크다운 렌더 (근본수정: 날것 노출 0)', () => {
  it('**굵게** → <strong>, 날것 ** 없음', () => {
    const { container } = render(<Markdown>{'**긍정 58.3%**로 높음'}</Markdown>);
    const strong = container.querySelector('strong');
    expect(strong).not.toBeNull();
    expect(strong?.textContent).toBe('긍정 58.3%');
    expect(container.textContent ?? '').not.toContain('**');
  });

  it('## 헤더 + 리스트 렌더, 마커 날것 없음', () => {
    const { container } = render(<Markdown>{'## 핵심\n- 항목1\n- 항목2'}</Markdown>);
    expect(container.querySelector('h4')).not.toBeNull(); // ## → h4 (디자인 토큰 매핑)
    expect(container.querySelectorAll('li')).toHaveLength(2);
    const txt = container.textContent ?? '';
    expect(txt).not.toContain('##');
    expect(txt).not.toContain('- 항목');
  });
});
