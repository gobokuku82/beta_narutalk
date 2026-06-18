import React from 'react';

export interface TableColumn<T> {
  key: string;
  label: string;
  render?: (value: any, row: T) => React.ReactNode;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

export interface TableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  onRowClick?: (row: T, index: number) => void;
  selectedRows?: number[];
  className?: string;
  emptyMessage?: string;
}

export function Table<T extends Record<string, any>>({
  columns,
  data,
  onRowClick,
  selectedRows = [],
  className = '',
  emptyMessage = '데이터가 없습니다',
}: TableProps<T>) {
  const [hoveredRow, setHoveredRow] = React.useState<number | null>(null);

  // 행 상태별 스타일 정의 (Default, Hover, Selected)
  const getRowStyles = (index: number) => {
    let styles = 'transition-all duration-150 ';

    if (selectedRows.includes(index)) {
      // Selected 상태
      styles += 'bg-accent/10 border-l-2 border-l-accent';
    } else if (hoveredRow === index) {
      // Hover 상태
      styles += 'bg-gray-50 shadow-sm';
    } else {
      // Default 상태
      styles += 'bg-white hover:bg-gray-50';
    }

    if (onRowClick) {
      styles += ' cursor-pointer';
    }

    return styles;
  };

  const getCellAlignment = (align?: 'left' | 'center' | 'right') => {
    switch (align) {
      case 'center':
        return 'text-center';
      case 'right':
        return 'text-right';
      default:
        return 'text-left';
    }
  };

  return (
    <div className={`overflow-x-auto rounded-lg border border-gray-200 ${className}`}>
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={`px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider ${getCellAlignment(column.align)}`}
                style={{ width: column.width }}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-12 text-center text-gray-500"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={getRowStyles(rowIndex)}
                onClick={() => onRowClick?.(row, rowIndex)}
                onMouseEnter={() => setHoveredRow(rowIndex)}
                onMouseLeave={() => setHoveredRow(null)}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={`px-4 py-3 text-sm text-gray-900 ${getCellAlignment(column.align)}`}
                  >
                    {column.render
                      ? column.render(row[column.key], row)
                      : row[column.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

// 테이블 행 컴포넌트 (개별 사용을 위해)
export const TableRow: React.FC<{
  children: React.ReactNode;
  selected?: boolean;
  onClick?: () => void;
  className?: string;
}> = ({ children, selected = false, onClick, className = '' }) => {
  const [isHovered, setIsHovered] = React.useState(false);

  const getStyles = () => {
    let styles = 'transition-all duration-150 ';

    if (selected) {
      styles += 'bg-accent/10 border-l-2 border-l-accent';
    } else if (isHovered) {
      styles += 'bg-gray-50 shadow-sm';
    } else {
      styles += 'bg-white';
    }

    if (onClick) {
      styles += ' cursor-pointer hover:bg-gray-50';
    }

    return styles;
  };

  return (
    <tr
      className={`${getStyles()} ${className}`}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {children}
    </tr>
  );
};

export default Table;