import { describe, it, expect, beforeEach } from 'vitest';
import { useAgent } from './store';
import type { WSMessage } from '@/api/schemas';

beforeEach(() => {
  useAgent.setState({ messages: [], nodeEvents: [] });
});

describe('agent store — attachments 배선 (다운로드 경로)', () => {
  it('complete 응답의 response.attachments(url 보유) → 메시지 attachments 로 추출', () => {
    const msg = {
      type: 'complete',
      data: {
        status: 'success',
        response: {
          text: '4월 분석 결과입니다.',
          format: 'ppt',
          attachments: [
            { kind: 'ppt', url: '/api/files/download?p=clumi/outputs/report_x.pptx', caption: '보고서' },
            { kind: 'chart', path: '/abs/x.png', url: null }, // url 없음 → 제외
          ],
        },
      },
    } as unknown as WSMessage;

    useAgent.getState().handleWSMessage(msg);
    const m = useAgent.getState().messages.at(-1)!;
    expect(m.role).toBe('assistant');
    expect(m.format).toBe('ppt');
    expect(m.attachments).toHaveLength(1); // url 없는 chart 는 빠짐
    expect(m.attachments![0]).toMatchObject({
      kind: 'ppt',
      url: expect.stringContaining('report_x.pptx'),
      caption: '보고서',
    });
  });

  it('attachments 없는 평범한 응답 → 기존 동작 보존 (빈 배열)', () => {
    const msg = {
      type: 'complete',
      data: { status: 'success', response: { text: '평범한 답변', format: 'text' } },
    } as unknown as WSMessage;

    useAgent.getState().handleWSMessage(msg);
    const m = useAgent.getState().messages.at(-1)!;
    expect(m.content).toBe('평범한 답변');
    expect(m.attachments ?? []).toHaveLength(0);
  });
});
