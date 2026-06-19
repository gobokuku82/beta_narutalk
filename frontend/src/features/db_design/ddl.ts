/**
 * DDL 생성기 — ERD 설계(ErdDesign) → PostgreSQL CREATE TABLE SQL.
 *
 * 출력은 dreamagent_data 구축에 바로 쓸 수 있는 DDL (사용자 결정: DDL 출력만, 자동 적용 X).
 * FK 는 column.fk(참조 테이블·컬럼)로부터 ALTER 가 아닌 인라인 제약으로 생성.
 */
import type { ErdDesign, ErdTable } from './store';

function quoteIdent(name: string): string {
  // 안전한 식별자(소문자/숫자/언더스코어)는 그대로, 아니면 큰따옴표.
  return /^[a-z_][a-z0-9_]*$/.test(name) ? name : `"${name.replace(/"/g, '""')}"`;
}

function columnLine(col: ErdTable['columns'][number]): string {
  const parts = [quoteIdent(col.name), col.type || 'TEXT'];
  if (!col.nullable) parts.push('NOT NULL');
  if (col.unique && !col.pk) parts.push('UNIQUE');
  if (col.default !== null && col.default !== undefined && String(col.default).trim() !== '') {
    parts.push(`DEFAULT ${col.default}`);
  }
  return '    ' + parts.join(' ');
}

function tableDDL(table: ErdTable): string {
  const lines: string[] = [];
  for (const col of table.columns) lines.push(columnLine(col));

  const pks = table.columns.filter((c) => c.pk).map((c) => quoteIdent(c.name));
  if (pks.length > 0) {
    lines.push(`    PRIMARY KEY (${pks.join(', ')})`);
  }

  // FK 제약 (인라인 — 참조 테이블이 같은 설계에 있을 때)
  for (const col of table.columns) {
    if (col.fk && col.fk.table && col.fk.column) {
      const cname = `fk_${table.name}_${col.name}`;
      lines.push(
        `    CONSTRAINT ${quoteIdent(cname)} FOREIGN KEY (${quoteIdent(col.name)}) ` +
          `REFERENCES ${quoteIdent(col.fk.table)} (${quoteIdent(col.fk.column)})`,
      );
    }
  }

  const comment = table.comment ? `-- ${table.comment}\n` : '';
  return `${comment}CREATE TABLE ${quoteIdent(table.name)} (\n${lines.join(',\n')}\n);`;
}

export function generateDDL(design: ErdDesign): string {
  if (!design.tables.length) {
    return '-- (테이블 없음) — 테이블을 추가하세요.';
  }
  const header =
    `-- ${design.name} DDL (PostgreSQL)\n` +
    `-- DreamAgent DB설계 페이지 생성. 자동 적용 안 됨 — 검토 후 수동 실행.\n`;
  const body = design.tables.map(tableDDL).join('\n\n');
  return `${header}\n${body}\n`;
}
