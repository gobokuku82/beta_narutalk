# _domains/ - 도메인 참조 코드 라이브러리

## 목적

검증된 Agent/Tool 구현체를 저장하는 참조 코드 라이브러리입니다.
`app/dream_agent/`에서 개발 시 템플릿으로 활용합니다.

## 구조

```
_domains/
├── agents/              # Agent 참조 구현
│   ├── data_agent/      # 데이터 수집/전처리 Agent
│   ├── analysis_agent/  # 분석 Agent
│   ├── content_agent/   # 콘텐츠 생성 Agent
│   └── ops_agent/       # 비즈니스 운영 Agent
│
└── tools/               # Tool 참조 구현
    ├── collectors/      # 데이터 수집기
    ├── analyzers/       # 분석기
    └── generators/      # 생성기
```

## 워크플로우

```
1. 새 브랜치에서 agent/tool 개발
   └── feature/data-collector

2. 검증 & 테스트 완료

3. _domains/에 참조 코드로 저장
   └── _domains/tools/collectors/amazon_collector.py

4. dream_agent/에서 가져다 쓰기
   └── execution/executors/data_executor.py에서 참조/복사
```

## 규칙

- **`_` 접두사**: Python import 대상에서 제외됨 (참조 전용)
- **직접 import 금지**: `from _domains import ...` 하지 않음
- **복사해서 사용**: 필요한 코드를 `dream_agent/`로 복사 후 수정
- **버전 표시**: 각 파일 상단에 버전, 작성일, 검증 상태 명시

## 파일 헤더 템플릿

```python
"""
[Agent/Tool 이름]

Version: 1.0.0
Date: 2026-02-05
Status: Verified | Draft | Deprecated
Branch: feature/xxx (원본 개발 브랜치)

Description:
    ...

Usage:
    dream_agent/execution/executors/에 복사하여 사용
"""
```
