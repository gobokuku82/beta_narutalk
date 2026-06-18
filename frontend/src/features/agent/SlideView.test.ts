import { describe, it, expect } from 'vitest';
import { parseSlides } from './SlideView';

describe('parseSlides — 마크다운 → 슬라이드 (Phase3 채팅창 시각화)', () => {
  it('# = 표지, ## = 섹션 + 본문(마크다운 보존)', () => {
    const md = '# 4월 보고서\n\n## 핵심 성과\n- 매출 1.2억\n- 재구매 상승\n\n## 채널\n- naver 우위';
    const slides = parseSlides(md);
    expect(slides).toHaveLength(3);
    expect(slides[0]).toMatchObject({ title: '4월 보고서', cover: true });
    expect(slides[1]!.title).toBe('핵심 성과');
    expect(slides[1]!.body).toContain('매출 1.2억');
    expect(slides[1]!.body).toContain('재구매 상승');
    expect(slides[2]!.body).toContain('naver 우위');
  });

  it('헤더 없으면 결과 1장 fallback', () => {
    const slides = parseSlides('그냥 텍스트');
    expect(slides).toHaveLength(1);
    expect(slides[0]!.body).toContain('그냥 텍스트');
  });

  it('# 표지 + 본문 → 표지 body 에 / ## 섹션 분리', () => {
    const slides = parseSlides('# 제목\n도입 문장입니다\n## 본론\n- 항목');
    expect(slides[0]).toMatchObject({ title: '제목', cover: true });
    expect(slides[0]!.body).toContain('도입 문장입니다');
    expect(slides[1]!.title).toBe('본론');
  });
});
