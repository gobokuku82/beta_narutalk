/**
 * DataTable — 표 = 시각화 (통합계획서 §5.7 / 원칙 P5).
 *
 * Status: complete — 정렬 + in-cell 막대 + 히트 + 합계/평균.
 *
 * 맨 HTML 표를 대체:
 *  - 컬럼별 정렬 (헤더 클릭, useState 기반)
 *  - in-cell 막대 (column.bar) — 값 비교를 셀 안에서 시각적으로 (P5)
 *  - in-cell 히트 (column.heat) — 좋음/나쁨 임계 기반 셀 텍스트 색
 *  - 합계·평균 행 (footerSum / footerAvg)
 *  - tabular-nums · hairline 보더 · hover 강조
 */
import { useMemo, useState, type ReactNode } from 'react';
import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react';
import { cn } from '@/lib/cn';

export interface DataTableColumn<T> {
  key: string;
  label: string;
  align?: 'left' | 'right' | 'center';
  /** 셀 표시 형식 변환. */
  format?: (value: unknown, row: T) => ReactNode;
  /** 정렬 가능 여부 — default true. */
  sortable?: boolean;
  /** 값 추출 (key 가 row 의 직접 속성이 아니거나 가공이 필요할 때). */
  accessor?: (row: T) => number | string | null | undefined;
  /** P5: 셀 안 막대. */
  bar?: {
    /** 최대값 — 미지정 시 모든 행 기준 자동 계산. */
    max?: number;
    /** 막대 색 — default chart-1. */
    color?: string;
  };
  /** P5: 셀 히트 텍스트 색. */
  heat?: {
    /** 'high' = 높을수록 좋음(success), 'low' = 낮을수록 좋음(CPA 등). */
    direction: 'high' | 'low';
    /** good 임계 (포함). */
    goodAt: number;
    /** bad 임계 (포함). */
    badAt: number;
  };
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  defaultSort?: { key: string; desc?: boolean };
  /** 합계 행에 표시할 컬럼 키. */
  footerSum?: string[];
  /** 평균 행에 표시할 컬럼 키. */
  footerAvg?: string[];
  className?: string;
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  rows,
  defaultSort,
  footerSum,
  footerAvg,
  className,
}: DataTableProps<T>) {
  const [sort, setSort] = useState<{ key: string; desc: boolean } | null>(
    defaultSort ? { key: defaultSort.key, desc: !!defaultSort.desc } : null,
  );

  const getValue = (
    col: DataTableColumn<T>,
    row: T,
  ): number | string | null | undefined => {
    if (col.accessor) return col.accessor(row);
    const v = row[col.key];
    if (typeof v === 'number' || typeof v === 'string' || v == null) return v;
    return String(v);
  };

  const sortedRows = useMemo(() => {
    if (!sort) return rows;
    const col = columns.find((c) => c.key === sort.key);
    if (!col) return rows;
    const arr = [...rows];
    arr.sort((a, b) => {
      const va = getValue(col, a);
      const vb = getValue(col, b);
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (typeof va === 'number' && typeof vb === 'number') {
        return sort.desc ? vb - va : va - vb;
      }
      return sort.desc
        ? String(vb).localeCompare(String(va))
        : String(va).localeCompare(String(vb));
    });
    return arr;
  }, [rows, sort, columns]);

  const barMaxByCol = useMemo(() => {
    const m: Record<string, number> = {};
    for (const col of columns) {
      if (!col.bar) continue;
      if (col.bar.max != null) {
        m[col.key] = col.bar.max;
      } else {
        const values: number[] = [];
        for (const r of rows) {
          const v = getValue(col, r);
          if (typeof v === 'number') values.push(v);
        }
        m[col.key] = values.length ? Math.max(...values) : 1;
      }
    }
    return m;
  }, [columns, rows]);

  const toggleSort = (key: string) => {
    setSort((prev) => {
      if (!prev || prev.key !== key) return { key, desc: true };
      if (prev.desc) return { key, desc: false };
      return null;
    });
  };

  return (
    <div
      className={cn(
        // VOCABULARY.md §5 H6 — DataTable wrapper 는 hover state 미적용 (nested in ChartFrame 인 케이스가 대부분 — 외곽 ChartFrame 만 강조 받음, ring 짤림 회피, 2026-06-10 fix)
        'overflow-x-auto rounded-lg border border-border bg-card',
        className,
      )}
    >
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-muted-foreground">
            {columns.map((col) => {
              const isSorted = sort?.key === col.key;
              const sortable = col.sortable !== false;
              return (
                <th
                  key={col.key}
                  className={cn(
                    'px-3 py-2 font-medium',
                    col.align === 'right' && 'text-right',
                    col.align === 'center' && 'text-center',
                    sortable && 'cursor-pointer select-none hover:text-foreground',
                  )}
                  onClick={sortable ? () => toggleSort(col.key) : undefined}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {sortable &&
                      (isSorted ? (
                        sort!.desc ? (
                          <ArrowDown className="h-3 w-3" />
                        ) : (
                          <ArrowUp className="h-3 w-3" />
                        )
                      ) : (
                        <ArrowUpDown className="h-3 w-3 opacity-30" />
                      ))}
                  </span>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, i) => (
            <tr
              key={i}
              className="border-b border-border last:border-0 hover:bg-muted/30"
            >
              {columns.map((col) => {
                const value = getValue(col, row);
                const isBarCell = col.bar && typeof value === 'number';
                const barMax = isBarCell ? barMaxByCol[col.key] ?? 1 : 0;
                const pct = isBarCell && barMax > 0
                  ? Math.min(100, (Math.abs(value as number) / barMax) * 100)
                  : 0;
                return (
                  <td
                    key={col.key}
                    className={cn(
                      'relative px-3 py-2 tabular-nums',
                      col.align === 'right' && 'text-right',
                      col.align === 'center' && 'text-center',
                      col.heat &&
                        typeof value === 'number' &&
                        heatClass(col.heat, value),
                    )}
                  >
                    {isBarCell && (
                      <div
                        aria-hidden
                        className="absolute inset-y-1 rounded-sm"
                        style={{
                          width: `${pct}%`,
                          background: col.bar!.color ?? 'hsl(var(--chart-1))',
                          opacity: 0.15,
                          right: col.align === 'right' ? 4 : undefined,
                          left: col.align === 'right' ? undefined : 4,
                        }}
                      />
                    )}
                    <span className="relative">
                      {col.format
                        ? col.format(value, row)
                        : value == null
                          ? <span className="text-muted-foreground">—</span>
                          : String(value)}
                    </span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
        {((footerSum && footerSum.length > 0) ||
          (footerAvg && footerAvg.length > 0)) && (
          <tfoot>
            {footerSum && footerSum.length > 0 && (
              <FooterRow
                label="합계"
                columns={columns}
                rows={rows}
                keys={footerSum}
                reducer={(values) => values.reduce((a, b) => a + b, 0)}
              />
            )}
            {footerAvg && footerAvg.length > 0 && (
              <FooterRow
                label="평균"
                columns={columns}
                rows={rows}
                keys={footerAvg}
                reducer={(values) =>
                  values.length
                    ? values.reduce((a, b) => a + b, 0) / values.length
                    : 0
                }
              />
            )}
          </tfoot>
        )}
      </table>
    </div>
  );
}

function heatClass(
  heat: NonNullable<DataTableColumn<unknown>['heat']>,
  value: number,
): string | undefined {
  if (heat.direction === 'high') {
    if (value >= heat.goodAt) return 'text-success font-medium';
    if (value <= heat.badAt) return 'text-destructive';
  } else {
    if (value <= heat.goodAt) return 'text-success font-medium';
    if (value >= heat.badAt) return 'text-destructive';
  }
  return undefined;
}

function FooterRow<T extends Record<string, unknown>>({
  label,
  columns,
  rows,
  keys,
  reducer,
}: {
  label: string;
  columns: DataTableColumn<T>[];
  rows: T[];
  keys: string[];
  reducer: (values: number[]) => number;
}) {
  return (
    <tr className="border-t border-border bg-muted/40 text-xs font-medium">
      {columns.map((col, idx) => {
        if (idx === 0) {
          return (
            <td key={col.key} className="px-3 py-2 text-muted-foreground">
              {label}
            </td>
          );
        }
        if (!keys.includes(col.key)) {
          return <td key={col.key} className="px-3 py-2"></td>;
        }
        const values: number[] = [];
        for (const r of rows) {
          const v = col.accessor ? col.accessor(r) : r[col.key];
          if (typeof v === 'number') values.push(v);
        }
        const reduced = reducer(values);
        return (
          <td
            key={col.key}
            className={cn(
              'px-3 py-2 tabular-nums',
              col.align === 'right' && 'text-right',
              col.align === 'center' && 'text-center',
            )}
          >
            {col.format ? col.format(reduced, {} as T) : reduced.toString()}
          </td>
        );
      })}
    </tr>
  );
}
