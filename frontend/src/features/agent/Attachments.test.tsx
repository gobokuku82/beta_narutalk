import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Attachments } from './Attachments';

describe('Attachments — 다운로드 칩 (작은 칩)', () => {
  it('url 보유 attachment → 다운로드 링크 (절대 href + 파일종류 라벨)', () => {
    const { container } = render(
      <Attachments items={[{ kind: 'ppt', url: '/api/files/download?p=clumi/outputs/r.pptx' }]} />,
    );
    const a = container.querySelector('a')!;
    expect(a).not.toBeNull();
    expect(a.getAttribute('href')).toContain('/api/files/download?p=clumi/outputs/r.pptx');
    expect(a.hasAttribute('download')).toBe(true);
    expect(a.textContent).toContain('PPT'); // kind → 라벨 매핑
  });

  it('여러 산출물 → 칩 여러 개', () => {
    const { container } = render(
      <Attachments
        items={[
          { kind: 'ppt', url: '/api/files/download?p=a.pptx' },
          { kind: 'pdf', url: '/api/files/download?p=b.pdf' },
        ]}
      />,
    );
    expect(container.querySelectorAll('a')).toHaveLength(2);
  });

  it('빈/undefined → 아무것도 렌더하지 않음', () => {
    const { container: c1 } = render(<Attachments items={[]} />);
    expect(c1.querySelector('a')).toBeNull();
    const { container: c2 } = render(<Attachments />);
    expect(c2.querySelector('a')).toBeNull();
  });
});
