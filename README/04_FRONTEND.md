# 04. 프론트엔드 (HTML 대시보드)

## 개요

> **목적**: 백엔드 테스트용 HTML 대시보드

프론트엔드는 순수 HTML/CSS/JavaScript로 구성되어 있으며, 백엔드 API 테스트를 위한 간단한 대시보드입니다.

```
dashboard/
├── templates/
│   └── index.html          # 메인 대시보드 UI
└── static/
    ├── css/
    │   └── style.css       # 스타일링
    └── js/
        └── app.js          # WebSocket 클라이언트
```

---

## 3-Panel 레이아웃

```
┌───────────────────────────────────────────────────────────────────────────┐
│  Dream Agent                         Session: abc123...  [● Connected]    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────────┐│
│  │  Progress          [2]  │  │  Chat                     [중지] [초기화]││
│  │  ───────────────────────│  │  ────────────────────────────────────────││
│  │  ● 데이터 수집 - 실행중  │  │                                          ││
│  │    10:30:15             │  │  [System] Dream Agent에 오신 것을...     ││
│  │  ✓ 초기화 - 완료        │  │                                          ││
│  │    10:30:10             │  │  [User] 라네즈 리뷰 분석해줘             ││
│  │                   (RED) │  │                                          ││
│  ├─────────────────────────┤  │  [Agent] 분석을 시작합니다...            ││
│  │  Todo List         [4]  │  │                                          ││
│  │  ───────────────────────│  │                                          ││
│  │  ▸ 데이터 수집          │  │                                          ││
│  │    collector | ml_exec  │  │                                          ││
│  │  ▸ 전처리               │  │                                          ││
│  │    preprocessor | ml_exec│  │                                          ││
│  │  ▸ 감성 분석            │  │                                          ││
│  │    sentiment | ml_exec  │  │                                          ││
│  │  ▸ 인사이트 생성        │  │                                          ││
│  │    insight | ml_exec    │  │  ┌─────────────────────────────────────┐ ││
│  │                (YELLOW) │  │  │ 메시지를 입력하세요...       [전송] │ ││
│  └─────────────────────────┘  │  └─────────────────────────────────────┘ ││
│                               │                                    (BLUE)││
│                               └─────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────────────────┘
```

### 패널 구성

| 패널 | 색상 | 설명 |
|------|------|------|
| **Progress** | 빨간색 테두리 | 실행 중인 작업의 실시간 콜백 표시 |
| **Todo List** | 노란색 테두리 | 생성된 Todo 목록 표시 |
| **Chat** | 파란색 테두리 | 사용자-에이전트 대화 |

---

## HTML 구조 (index.html)

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Dream Agent Dashboard</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>Dream Agent</h1>
            <div class="header-right">
                <span class="session-badge" id="sessionBadge">Session: -</span>
                <span class="status-badge" id="connectionStatus">Disconnected</span>
            </div>
        </header>

        <!-- Main: 3-Panel Layout -->
        <main class="main">
            <!-- Left Column -->
            <div class="left-column">
                <!-- Progress (Red) -->
                <section class="panel-section progress-section">
                    <div class="panel-header">
                        <h3>Progress</h3>
                        <span class="badge" id="progressCount">0</span>
                    </div>
                    <div class="progress-list" id="progressList">
                        <p class="empty-state">실행 중인 작업이 없습니다.</p>
                    </div>
                </section>

                <!-- Todo (Yellow) -->
                <section class="panel-section todo-section">
                    <div class="panel-header">
                        <h3>Todo List</h3>
                        <span class="badge" id="todoCount">0</span>
                    </div>
                    <div class="todo-list" id="todoList">
                        <p class="empty-state">생성된 Todo가 없습니다.</p>
                    </div>
                </section>
            </div>

            <!-- Chat (Blue) -->
            <section class="chat-section">
                <div class="panel-header">
                    <h3>Chat</h3>
                    <div class="chat-controls">
                        <button id="stopBtn" class="btn-stop" disabled>중지</button>
                        <button id="clearBtn" class="btn-clear">초기화</button>
                    </div>
                </div>

                <div class="chat-messages" id="chatMessages">
                    <div class="message system">
                        <p>Dream Agent에 오신 것을 환영합니다.</p>
                    </div>
                </div>

                <form class="chat-input" id="chatForm">
                    <input type="text" id="userInput" placeholder="메시지를 입력하세요...">
                    <button type="submit" id="sendBtn">전송</button>
                </form>
            </section>
        </main>
    </div>

    <script src="/static/js/app.js"></script>
</body>
</html>
```

---

## JavaScript 클라이언트 (app.js)

### DreamAgentClient 클래스

```javascript
class DreamAgentClient {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.todos = [];
        this.progressItems = [];
    }

    // WebSocket 메시지 핸들러
    handleWSMessage(message) {
        switch (message.type) {
            case 'todo_update':
                this.handleTodoUpdate(message.data);
                break;
            case 'progress':
                this.handleProgress(message.data);
                break;
            case 'complete':
                this.handleComplete(message.data);
                break;
            case 'error':
                this.handleError(message.data);
                break;
        }
    }

    // Todo 업데이트 → Todo 패널 + Progress 패널
    handleTodoUpdate(data) {
        // Todo 리스트 업데이트
        if (data.todos) {
            this.todos = data.todos;
        }
        this.renderTodoList();

        // in_progress 상태면 Progress에 추가
        if (data.todo?.status === 'in_progress') {
            this.addProgressItem({
                id: data.todo.id,
                task: data.todo.task,
                status: 'running',
                time: new Date().toLocaleTimeString(),
            });
        }
    }

    // Progress 콜백 → Progress 패널
    handleProgress(data) {
        this.addProgressItem({
            id: data.id,
            task: data.message,
            status: data.status,
            time: new Date().toLocaleTimeString(),
        });
    }
}
```

### Progress 패널 렌더링

```javascript
renderProgressList() {
    const el = this.elements.progressList;
    const runningCount = this.progressItems.filter(p => p.status === 'running').length;

    this.elements.progressCount.textContent = runningCount;

    el.innerHTML = this.progressItems.map(item => `
        <div class="progress-item ${item.status}">
            <div class="task-name">
                ${item.status === 'running' ? '<span class="loading"></span>' : ''}
                ${item.task}
            </div>
            <div class="task-status">${this.getStatusText(item.status)}</div>
            <div class="task-time">${item.time}</div>
        </div>
    `).join('');
}
```

### Todo 패널 렌더링

```javascript
renderTodoList() {
    const el = this.elements.todoList;

    this.elements.todoCount.textContent = this.todos.length;

    el.innerHTML = this.todos.map(todo => `
        <div class="todo-item ${todo.status}">
            <div class="task">${todo.task}</div>
            <div class="meta">
                <span class="tool">${todo.metadata?.execution?.tool || ''}</span>
                <span class="layer">${todo.layer || ''}</span>
            </div>
        </div>
    `).join('');
}
```

---

## CSS 스타일 요약

### 레이아웃

```css
/* 3-Panel Grid */
.main {
    display: grid;
    grid-template-columns: 380px 1fr;  /* Left: 380px, Right: Chat */
    gap: 16px;
}

.left-column {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

/* Progress: 35% 높이 */
.progress-section {
    flex: 0 0 auto;
    max-height: 35%;
    border: 2px solid #ef5350;  /* Red */
}

/* Todo: 나머지 공간 */
.todo-section {
    flex: 1;
    border: 2px solid #ffa726;  /* Yellow/Orange */
}

/* Chat: 오른쪽 전체 */
.chat-section {
    border: 2px solid #42a5f5;  /* Blue */
}
```

### 패널 색상 테마

```css
/* Progress (Red Theme) */
.progress-section .panel-header {
    background: linear-gradient(135deg, #ffebee 0%, #fff 100%);
}
.progress-section .panel-header h3 { color: #c62828; }
.progress-section .badge { background: #ef5350; color: white; }

/* Todo (Yellow Theme) */
.todo-section .panel-header {
    background: linear-gradient(135deg, #fff8e1 0%, #fff 100%);
}
.todo-section .panel-header h3 { color: #e65100; }
.todo-section .badge { background: #ffa726; color: white; }

/* Chat (Blue Theme) */
.chat-section .panel-header {
    background: linear-gradient(135deg, #e3f2fd 0%, #fff 100%);
}
.chat-section .panel-header h3 { color: #1565c0; }
```

### 상태별 스타일

```css
/* Progress Item */
.progress-item.running {
    border-left-color: #2196f3;
    background: #e3f2fd;
    animation: pulse 1.5s infinite;
}
.progress-item.completed { border-left-color: #4caf50; background: #e8f5e9; }
.progress-item.failed { border-left-color: #f44336; background: #ffebee; }

/* Todo Item */
.todo-item.pending { border-left-color: #ffa726; background: #fffaf0; }
.todo-item.in_progress { border-left-color: #2196f3; background: #e3f2fd; }
.todo-item.completed { border-left-color: #4caf50; background: #e8f5e9; opacity: 0.7; }
.todo-item.failed { border-left-color: #f44336; background: #ffebee; }
```

---

## WebSocket 메시지 타입

### Server → Client

| 타입 | 설명 | Progress 패널 | Todo 패널 |
|------|------|---------------|-----------|
| `todo_update` | Todo 상태 변경 | in_progress → 추가 | 목록 갱신 |
| `progress` | 실행 콜백 | 항목 추가/업데이트 | - |
| `complete` | 실행 완료 | 모두 완료 처리 | - |
| `error` | 오류 발생 | 실패 표시 | - |

### 데이터 형식

```javascript
// todo_update
{
    "type": "todo_update",
    "data": {
        "todo": {
            "id": "uuid",
            "task": "데이터 수집",
            "status": "in_progress",
            "metadata": { "execution": { "tool": "collector" } },
            "layer": "ml_execution"
        }
    }
}

// progress (실행 콜백)
{
    "type": "progress",
    "data": {
        "id": "task-id",
        "message": "Amazon에서 리뷰 수집 중...",
        "status": "running",
        "detail": "50/100 수집"
    }
}
```

---

## 접속 방법

```bash
# 1. 백엔드 서버 실행
cd backend
uvicorn api.main:app --reload --port 8000

# 2. 브라우저에서 접속
http://localhost:8000
```

---

## 향후 개선사항

- [ ] React/Vue 기반 SPA로 전환
- [ ] Progress 실시간 차트 (진행률 바)
- [ ] Todo 드래그앤드롭 재정렬
- [ ] 히스토리 저장/불러오기
- [ ] 다크모드 지원
- [ ] 반응형 디자인 (모바일)
