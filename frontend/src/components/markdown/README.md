# markdown (placeholder)

POC 단계 미구현. chat 답변 markdown 렌더링 진입 시 활성화.

- 의도: agent 응답에 포함된 markdown (`**굵게**`, `# 제목`, 표 등) 을 안전하게 HTML 로 렌더링
- 라이브러리: `react-markdown` + `remark-gfm` (`package.json` 박제, 미사용)
- 진입 시 사용 위치 후보: `features/agent/` chat bubble 컴포넌트
- 2026-06-02 작업 1번: 빈 폴더 + `.gitkeep` 잔존 → README 박제로 의도 명시
