/**
 * turnsToMessages 단위 테스트 — 대화 복원 매핑 (세션 연속성 P2).
 *
 * 설계: docs/reports/세션연속성_복원_설계계획_2026-06-11.md §4
 */
import { describe, expect, it } from 'vitest';
import { turnsToMessages } from './restore';
import type { ConversationTurns } from '@/api/hooks/useConversations';

function turns(items: ConversationTurns['items']): ConversationTurns {
  return { conversation_id: 'conv_1', items, total: items.length };
}

describe('turnsToMessages', () => {
  it('빈 대화 → 빈 배열', () => {
    expect(turnsToMessages(turns([]))).toEqual([]);
  });

  it('여러 turn 을 평탄화하고 turn별 안정 id 부여', () => {
    const out = turnsToMessages(
      turns([
        {
          turn_id: 'turn_a',
          status: 'completed',
          created_at: '2026-04-01T00:00:00Z',
          messages: [
            { role: 'user', content: '안녕' },
            { role: 'assistant', content: '네' },
          ],
        },
        {
          turn_id: 'turn_b',
          status: 'completed',
          created_at: '2026-04-02T00:00:00Z',
          messages: [{ role: 'user', content: '또' }],
        },
      ]),
    );
    expect(out).toHaveLength(3);
    expect(out[0]).toMatchObject({ id: 'restored_turn_a_0', role: 'user', content: '안녕' });
    expect(out[1]).toMatchObject({ id: 'restored_turn_a_1', role: 'assistant', content: '네' });
    expect(out[2]).toMatchObject({ id: 'restored_turn_b_0', role: 'user', content: '또' });
    // timestamp = turn.created_at
    expect(out[0]?.timestamp).toBe('2026-04-01T00:00:00Z');
  });

  it('format 전달 + null → undefined 정규화', () => {
    const out = turnsToMessages(
      turns([
        {
          turn_id: 't',
          status: 'completed',
          created_at: null,
          messages: [
            { role: 'assistant', content: 'ppt', format: 'ppt' },
            { role: 'assistant', content: 'plain', format: null },
          ],
        },
      ]),
    );
    expect(out[0]?.format).toBe('ppt');
    expect(out[1]?.format).toBeUndefined();
    expect(out[0]?.timestamp).toBe(''); // created_at null → ''
  });

  it('attachments — url 있는 것만, url 없는 건 제거', () => {
    const out = turnsToMessages(
      turns([
        {
          turn_id: 't',
          status: 'completed',
          created_at: null,
          messages: [
            {
              role: 'assistant',
              content: '보고서',
              attachments: [
                { kind: 'pdf', url: '/api/files/download?p=a', caption: '리포트' },
                { kind: 'chart' }, // url 없음 → 제거
              ],
            },
          ],
        },
      ]),
    );
    expect(out[0]?.attachments).toEqual([
      { kind: 'pdf', url: '/api/files/download?p=a', caption: '리포트' },
    ]);
  });
});
