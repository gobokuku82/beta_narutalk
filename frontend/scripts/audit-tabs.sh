#!/usr/bin/env bash
# audit-tabs.sh — Sidebar tab path ↔ router path 정합 검증.
#
# spec_64 §4.2 Enforcement.
# routes/README.md §실험·버전 라우트 컨벤션 ([tag] 패턴) 의 자동 검증.
#
# 검사 항목:
#  1. store.ts 의 SYSTEM_TABS / CLIENT_TABS 의 모든 path 가 router.tsx 에 createRoute 로 등록되었는가
#  2. router.tsx 의 createRoute path 중 store 에도 sidebar 도 없는 orphan 라우트 (settings·index 제외)
#  3. ICON_MAP 에 있는데 store TABS 에서 사용 안 하는 unused 아이콘
#
# 사용: pnpm audit:tabs (또는 pnpm audit:all — tokens + tabs 통합)
# Exit code: 0 (정합) / 1 (위반 발견)

set -e
cd "$(dirname "$0")/.."

FAIL=0
STORE=src/features/navigation/store.ts
ROUTER=src/routes/router.tsx
SIDEBAR=src/components/layout/Sidebar.tsx

echo "═══ Sidebar / Router 정합 audit ═══"
echo

# 1. store TABS 의 path 추출 (라인 패턴: path: '/...')
STORE_PATHS=$(grep -oE "path: '/[a-z-]*'" "$STORE" | sed -E "s/path: '(.*)'/\1/" | sort -u)
ROUTER_PATHS=$(grep -oE "path: '/[a-z-]*'" "$ROUTER" | sed -E "s/path: '(.*)'/\1/" | sort -u)
ROUTER_PATHS_WITH_INDEX=$(echo -e "/\n$ROUTER_PATHS" | sort -u)

# 1a. store path 가 router 에 없는 경우 (orphan tab — 사이드바 클릭 시 404)
ORPHAN_TABS=$(comm -23 <(echo "$STORE_PATHS") <(echo "$ROUTER_PATHS"))
echo "  [1] store TABS path → router 등록 확인 …"
if [ -n "$ORPHAN_TABS" ]; then
  echo "    FAIL — 사이드바에 있으나 라우트 없음 (클릭 시 404):"
  echo "$ORPHAN_TABS" | sed 's/^/      /'
  FAIL=$((FAIL + 1))
else
  echo "    OK ($(echo "$STORE_PATHS" | wc -l) tab path 모두 router 등록)"
fi

# 2. router 에 있는데 store TABS + settings + index 모두 아닌 경우 (접근 불가 라우트 — 정상이지만 확인)
SIDEBAR_PATHS=$(echo -e "$STORE_PATHS\n/settings\n/" | sort -u)
ORPHAN_ROUTES=$(comm -23 <(echo "$ROUTER_PATHS") <(echo "$SIDEBAR_PATHS"))
echo
echo "  [2] router path → sidebar/settings/index 표시 확인 …"
if [ -n "$ORPHAN_ROUTES" ]; then
  echo "    WARN — 라우트만 있고 어디서도 navigate 안 됨 (사이드바·설정·index 모두 아님):"
  echo "$ORPHAN_ROUTES" | sed 's/^/      /'
  echo "    (의도된 hidden 라우트라면 무시 가능 — settings 외 직접 navigate 호출 확인)"
else
  echo "    OK (모든 router path 가 sidebar 또는 settings/index)"
fi

# 3. ICON_MAP 키 추출
ICON_MAP_KEYS=$(awk '/^const ICON_MAP/,/^\};/' "$SIDEBAR" | grep -oE '^\s+[A-Z][a-zA-Z0-9]*' | sed -E 's/^\s+//' | sort -u)
USED_ICONS=$(grep -oE "iconName: '[A-Z][a-zA-Z0-9]*'" "$STORE" | sed -E "s/iconName: '(.+)'/\1/" | sort -u)
UNUSED_ICONS=$(comm -23 <(echo "$ICON_MAP_KEYS") <(echo "$USED_ICONS"))
echo
echo "  [3] ICON_MAP 사용 확인 …"
if [ -n "$UNUSED_ICONS" ]; then
  # 일부 아이콘은 다른 컴포넌트 (TopBar 등) 에서 사용 — WARN 만
  echo "    WARN — Sidebar ICON_MAP 에 등록했으나 store TABS 에서 사용 안 함:"
  echo "$UNUSED_ICONS" | sed 's/^/      /'
  echo "    (다른 컴포넌트 사용 또는 [tag] 폐기 후 잔존 — grep 으로 확인)"
else
  echo "    OK (모든 ICON_MAP 키가 store TABS 에서 사용)"
fi

echo
echo "═══════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
  echo "❌ $FAIL 정합 위반 발견"
  exit 1
fi
echo "✅ Sidebar / Router 정합"
