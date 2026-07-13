/**
 * ErdCanvas — ERD 시각화/편집 (React Flow).
 *
 * 노드 = 테이블(TableNode), 엣지 = FK 관계(column.fk 로부터 파생).
 * 엣지는 **칼럼↔칼럼**: FK 칼럼의 핸들 → 참조 PK 칼럼의 핸들. 위치 기반으로 가까운 면을 골라
 * 선이 빙 돌지 않게 한다. 칼럼 핸들끼리 드래그(connect) → 그 칼럼에 직접 FK 지정(새 칼럼 X).
 * 드래그 종료 → store.moveTable(위치 저장), 노드 클릭 → store.setSelected(우측 패널 편집).
 * store 가 단일 진실 소스 — 캔버스는 store 변경 시 재동기화.
 */
import { useEffect, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  ConnectionMode,
  useNodesState,
  useEdgesState,
  type Node as RFNode,
  type Edge as RFEdge,
  type Connection,
  type NodeChange,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useDbDesign, type ErdTable } from './store';
import { erdNodeTypes } from './TableNode';

function toNode(table: ErdTable): RFNode {
  return {
    id: table.id,
    type: 'table',
    position: table.position,
    data: { table },
  };
}

/** 핸들 id (`${colId}:l|r`) 에서 칼럼 id 추출. */
function colIdOfHandle(handle: string | null | undefined): string | null {
  if (!handle) return null;
  const i = handle.lastIndexOf(':');
  return i >= 0 ? handle.slice(0, i) : handle;
}

function buildEdges(tables: ErdTable[]): RFEdge[] {
  const byName = new Map(tables.map((t) => [t.name, t]));
  const edges: RFEdge[] = [];
  for (const t of tables) {
    for (const c of t.columns) {
      if (!c.fk || !c.fk.table) continue;
      const tgt = byName.get(c.fk.table);
      if (!tgt) continue;
      const tgtCol =
        tgt.columns.find((x) => x.name === c.fk?.column) ??
        tgt.columns.find((x) => x.pk) ??
        tgt.columns[0];
      if (!tgtCol) continue;
      // 소스 테이블이 타겟의 왼쪽이면 소스=오른쪽면·타겟=왼쪽면 → 선이 마주보게(안 꼬임).
      // 타입 일치 필수: source 끝은 source 핸들, target 끝은 target 핸들에 붙어야 렌더됨.
      const srcOnLeft = t.position.x <= tgt.position.x;
      edges.push({
        id: `${t.id}:${c.id}`,
        source: t.id,
        target: tgt.id,
        sourceHandle: srcOnLeft ? `${c.id}:sr` : `${c.id}:sl`,
        targetHandle: srcOnLeft ? `${tgtCol.id}:tl` : `${tgtCol.id}:tr`,
        type: 'smoothstep',
        label: c.name,
        animated: false,
      });
    }
  }
  return edges;
}

export function ErdCanvas() {
  const tables = useDbDesign((s) => s.tables);
  const moveTable = useDbDesign((s) => s.moveTable);
  const updateColumn = useDbDesign((s) => s.updateColumn);
  const setSelected = useDbDesign((s) => s.setSelected);

  const rfEdges = useMemo(() => buildEdges(tables), [tables]);

  const [nodes, setNodes, onNodesChange] = useNodesState<RFNode>(tables.map((t) => toNode(t)));
  const [edges, setEdges] = useEdgesState(rfEdges);

  // store 변경(테이블/컬럼 추가·편집) → 캔버스 재동기화.
  // ⚠️ 노드를 통째로 교체(setNodes(tables.map(toNode)))하면, 새 노드 객체엔 measured 가 없어서
  // React Flow(adoptUserNodes/parseHandles)가 매 store 변경마다 handleBounds 를 초기화한다.
  // → 엣지 끝점이 핸들을 잃고 노드 원점으로 떨어져 "선이 칼럼에서 떨어져 떠 보임".
  // 그래서 기존 노드에 in-place 병합해 measured/handleBounds 를 보존한다.
  useEffect(() => {
    setNodes((prev) => {
      const byId = new Map(prev.map((n) => [n.id, n]));
      return tables.map((t) => {
        const old = byId.get(t.id);
        return old ? { ...old, position: t.position, data: { table: t } } : toNode(t);
      });
    });
  }, [tables, setNodes]);

  useEffect(() => setEdges(rfEdges), [rfEdges, setEdges]);

  // 칼럼 핸들끼리 연결 → 소스 칼럼에 FK 지정(타겟 칼럼을 참조). FK 칼럼 → PK 칼럼 방향으로 드래그.
  const onConnect = (conn: Connection) => {
    const srcColId = colIdOfHandle(conn.sourceHandle);
    const tgtColId = colIdOfHandle(conn.targetHandle);
    if (!conn.source || !conn.target || !srcColId || !tgtColId) return;
    if (conn.source === conn.target && srcColId === tgtColId) return; // 자기 자신 X
    const tgtTable = tables.find((t) => t.id === conn.target);
    const tgtCol = tgtTable?.columns.find((c) => c.id === tgtColId);
    if (!tgtTable || !tgtCol) return;
    updateColumn(conn.source, srcColId, { fk: { table: tgtTable.name, column: tgtCol.name } });
  };

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={erdNodeTypes}
        connectionMode={ConnectionMode.Loose}
        onNodesChange={(changes: NodeChange[]) => onNodesChange(changes)}
        fitView
        nodesDraggable
        nodesConnectable
        elementsSelectable
        proOptions={{ hideAttribution: true }}
        onNodeClick={(_e, n: RFNode) => setSelected(n.id)}
        onPaneClick={() => setSelected(null)}
        onNodeDragStop={(_e, n: RFNode) => moveTable(n.id, { x: n.position.x, y: n.position.y })}
        onConnect={onConnect}
      >
        <Background gap={16} className="!bg-background" />
        <Controls showInteractive={false} />
        <MiniMap pannable zoomable className="!bg-card !border !border-border" />
      </ReactFlow>
    </div>
  );
}
