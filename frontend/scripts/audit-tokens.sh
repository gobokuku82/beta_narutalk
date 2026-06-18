#!/usr/bin/env bash
# Phase 7 Enforcement — Design System 토큰 정합 audit (grep-based).
#
# spec_64 §4.2 Audit & Enforcement.
# ESLint plugin (eslint-plugin-tailwindcss) 는 pnpm/Windows 환경 호환 이슈로 보류.
# 본 스크립트가 plugin 대체 — CI / pre-commit 에서 호출 가능.
#
# 사용: pnpm audit:tokens
# Exit code: 0 (정합) / 1 (위반 발견)

set -e
cd "$(dirname "$0")/.."

FAIL=0

check() {
  local label="$1"
  local pattern="$2"
  local rule="$3"
  echo -n "  $label … "
  # shellcheck disable=SC2086
  local hits
  hits=$(grep -rnE "$pattern" src --include='*.tsx' --include='*.ts' 2>/dev/null | grep -vE 'src/components/ui/' || true)
  if [ -n "$hits" ]; then
    echo "FAIL ($rule)"
    echo "$hits" | head -10
    FAIL=$((FAIL + 1))
  else
    echo "OK"
  fi
}

echo "═══ Design System 토큰 정합 audit ═══"
echo
echo "[TYPOGRAPHY]"
check "T1 임의값 text-[Npx] 금지"        'text-\[[0-9]+px\]' 'TYPOGRAPHY.md T1'

echo
echo "[SPACING]"
check "S2 half step (1.5) 금지"          '\b(p|py|px|gap|space-[xy])-(0|1)\.5\b' 'SPACING.md S2'
check "S3 sub-grid (0.5) 금지"            '\b(p|py|px|gap|space-[xy])-0\.5\b' 'SPACING.md S3'

echo
echo "[RADIUS]"
check "R3 rounded (no suffix) 금지"      "[\"' ]rounded[\"' ]" 'RADIUS.md R3'

echo
echo "[ELEVATION]"
check "E2 큰 shadow blur (xl/2xl) 금지"  '\bshadow-(xl|2xl)\b' 'ELEVATION.md E2'

echo
echo "═══════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
  echo "❌ $FAIL 위반 발견 — spec 64 § 메타룰 MR1 위반"
  exit 1
fi
echo "✅ 모든 룰 정합"
