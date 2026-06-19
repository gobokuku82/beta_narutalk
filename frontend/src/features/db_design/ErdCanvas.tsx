/**
 * ErdCanvas — ERD 시각화/편집 (React Flow).
 *
 * 노드 = 테이블(TableNode), 엣지 = FK 관계(column.fk 로부터 파생).
 * 드래그 종료 → store.moveTable(위치 저장), Handle 연결 → store.connect(FK 컬럼 추가),
 * 노드 클릭 → store.setSelected(우측 패널 편집).
 * store 가 단일 진실 소스 — 캔버스는 store 변경 시 재동기화.
 */
import { useEffect, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
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

function buildEdges(tables: ErdTable[]): RFEdge[] {
  const nameToId = new Map(tables.map((t) => [t.name, t.id]));
  const edges: RFEdge[] = [];
  for (const t of tables) {
    for (const c of t.columns) {
      if (c.fk && c.fk.table) {
        const targetId = nameToId.get(c.fk.table);
        if (targetId) {
          edges.push({
            id: `${t.id}:${c.id}`,
            source: t.id,
            target: targetId,
            label: c.name,
            animated: false,
          });
        }
      }
    }
  }
  return edges;
}

export function ErdCanvas() {
  const tables = useDbDesign((s) => s.tables);
  const moveTable = useDbDesign((s) => s.moveTable);
  const connect = useDbDesign((s) => s.connect);
  const setSelected = useDbDesign((s) => s.setSelected);

  const rfNodes = useMemo(() => tables.map(toNode), [tables]);
  const rfEdges = useMemo(() => buildEdges(tables), [tables]);

  const [nodes, setNodes, onNodesChange] = useNodesState(rfNodes);
  const [edges, setEdges] = useEdgesState(rfEdges);

  // store 변경(테이블/컬럼 추가·편집) → 캔버스 재동기화
  useEffect(() => setNodes(rfNodes), [rfNodes, setNodes]);
  useEffect(() => setEdges(rfEdges), [rfEdges, setEdges]);

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={erdNodeTypes}
        onNodesChange={(changes: NodeChange[]) => onNodesChange(changes)}
        fitView
        nodesDraggable
        nodesConnectable
        elementsSelectable
        proOptions={{ hideAttribution: true }}
        onNodeClick={(_e, n: RFNode) => setSelected(n.id)}
        onPaneClick={() => setSelected(null)}
        onNodeDragStop={(_e, n: RFNode) => moveTable(n.id, { x: n.position.x, y: n.position.y })}
        onConnect={(c: Connection) => {
          if (!c.source || !c.target || c.source === c.target) return;
          connect(c.source, c.target);
        }}
      >
        <Background gap={16} className="!bg-background" />
        <Controls showInteractive={false} />
        <MiniMap pannable zoomable className="!bg-card !border !border-border" />
      </ReactFlow>
    </div>
  );
}
