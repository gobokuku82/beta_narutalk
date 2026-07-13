/**
 * TableNode — ERD 캔버스의 테이블 카드 (React Flow 커스텀 노드).
 *
 * 헤더(테이블명) + 컬럼 목록(PK 🔑 / FK 🔗 / NN / UQ 배지).
 * **칼럼마다** 좌·우 연결점(Handle)을 둬서 FK 를 칼럼↔칼럼으로 잇는다(ConnectionMode.Loose).
 * 좌=muted, 우=accent. 캔버스(ErdCanvas)가 위치 기반으로 가까운 면을 골라 선을 그린다.
 */
import { memo, useEffect, type CSSProperties } from 'react';
import { Handle, Position, useUpdateNodeInternals, type NodeProps } from '@xyflow/react';
import { cn } from '@/lib/cn';
import type { ErdTable } from './store';

export interface TableNodeData {
  table: ErdTable;
  [key: string]: unknown;
}

// 칼럼 행 가장자리를 덮는 "투명 연결점" — 점은 안 보이고 행 자체가 연결점.
// 선은 칼럼에 딱 붙고, 가장자리에 마우스 올리면 십자 커서로만 힌트.
const DOT = '!h-6 !w-3 !min-w-0 !rounded-none !border-0 !bg-transparent !cursor-crosshair';
// React Flow 기본 handle transform 은 translate(±50%, -50%) 라 핸들이 테두리 바깥으로 폭/2 만큼
// 삐져나가고, 엣지가 그 바깥 모서리에 붙어 틈이 생긴다. X 이동을 빼서 카드 안에 머물게 한다.
const FLUSH: CSSProperties = { transform: 'translateY(-50%)' };

function TableNodeComponent({ id, data, selected }: NodeProps) {
  const updateNodeInternals = useUpdateNodeInternals();
  const { table } = data as unknown as TableNodeData;
  // 칼럼(핸들) 구성이 바뀌면 React Flow 에 핸들 위치 재측정 요청.
  // 없으면 엣지가 칼럼 핸들을 못 찾아 노드 기본 위치(중앙)에 붙어 끊겨 보인다.
  const colKey = table.columns.map((c) => c.id).join('|');
  useEffect(() => {
    // 레이아웃 후(rAF) 재측정 — 첫 프레임에 stale 핸들 위치가 남지 않게.
    const raf = requestAnimationFrame(() => updateNodeInternals(id));
    return () => cancelAnimationFrame(raf);
  }, [id, colKey, updateNodeInternals]);

  return (
    <div
      className={cn(
        'group min-w-[200px] rounded-input border bg-card text-card-foreground',
        selected ? 'border-accent-action ring-1 ring-accent-action/40' : 'border-border',
      )}
    >
      <div className="rounded-t-input border-b border-border bg-muted/50 px-3 py-1">
        <span className="text-sm font-semibold">{table.name || '(unnamed)'}</span>
      </div>

      <ul className="flex flex-col py-1">
        {table.columns.length === 0 && (
          <li className="px-3 py-1 text-2xs text-muted-foreground">(컬럼 없음)</li>
        )}
        {table.columns.map((c) => (
          <li
            key={c.id}
            className="relative flex items-center justify-between gap-2 px-3 py-1 text-2xs"
          >
            {/* 칼럼마다 좌·우에 투명 target/source 핸들 — 행 가장자리가 곧 연결점(점 안 보임).
                React Flow 기본 translate(±50%) 의 바깥 X 이동을 제거(translateY 만) → 핸들이 카드 안에
                머물러 엣지가 테두리에 딱 붙는다(바깥으로 삐져나가 7px 틈 생기던 문제 해결). */}
            <Handle type="target" position={Position.Left} id={`${c.id}:tl`} className={DOT} style={FLUSH} />
            <Handle type="source" position={Position.Left} id={`${c.id}:sl`} className={DOT} style={FLUSH} />
            <Handle type="target" position={Position.Right} id={`${c.id}:tr`} className={DOT} style={FLUSH} />
            <Handle type="source" position={Position.Right} id={`${c.id}:sr`} className={DOT} style={FLUSH} />

            <span className="flex items-center gap-1 truncate">
              <span className="w-3 shrink-0 text-center">{c.pk ? '🔑' : c.fk ? '🔗' : ''}</span>
              <span className={cn('truncate', c.pk && 'font-semibold')}>{c.name}</span>
            </span>
            <span className="flex shrink-0 items-center gap-1 font-mono text-muted-foreground">
              <span>{c.type}</span>
              {!c.nullable && <span className="text-charcoal">NN</span>}
              {c.unique && !c.pk && <span className="text-accent-action-deep">UQ</span>}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export const TableNode = memo(TableNodeComponent);

export const erdNodeTypes = { table: TableNode };
