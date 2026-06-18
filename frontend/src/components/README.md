# components/ — 도메인 무관 공유 컴포넌트

도메인-유관 컴포넌트는 `features/{domain}/` 으로. **여기엔 도메인 모르는 공유만**.

## 폴더

| 폴더 | 역할 | 출처 |
|------|------|------|
| `ui/` | shadcn/ui primitives (button / dialog / ...) | `npx shadcn@latest add ...` |
| `layout/` | GlobalLayout / TopBar / Sidebar / Workspace | spec 61 §2 |
| `markdown/` | MarkdownRenderer (react-markdown + remark-gfm) | spec 61 §3.3 |

## shadcn/ui 설치 (Sprint 0 최초 1회)

```bash
pnpm dlx shadcn@latest init
pnpm dlx shadcn@latest add button dialog dropdown-menu input select tabs tooltip toast resizable sheet form card badge separator scroll-area textarea
```

설치 후 `ui/` 폴더에 button.tsx 등 생성됨. 디자인 토큰 (tailwind.config.ts / globals.css) 로 통합.

## 컨벤션

- 도메인 로직 X — props 받고 렌더링만
- shadcn/ui primitives 위에 더 작은 wrapper 가 필요하면 features 안에
- 디자인 변경 = tailwind config / globals.css 수정 (컴포넌트 직접 변경 X)
