// spec 64 §4.2 Enforcement — ESLint plugin (eslint-plugin-tailwindcss) 시도 결과:
//  pnpm/Windows 환경에서 tailwind-api-utils 의 config resolution 실패 (Could not resolve tailwindcss).
//  설치는 보존 (미래 plugin v4 또는 환경 개선 시 재시도). 비활성화 상태.
// 대안 = scripts/audit-tokens.sh (grep-based), pnpm audit:tokens 로 실행.
module.exports = {
  root: true,
  env: { browser: true, es2022: true, node: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    // 'plugin:tailwindcss/recommended',  // 보류 — pnpm/Windows 호환 이슈
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs', 'playwright-report', 'coverage'],
  parser: '@typescript-eslint/parser',
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
  },
};
