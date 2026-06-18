/**
 * React Flow NodeTypes 매핑 — task/branch/join/start/end.
 *
 * 본 파일은 *시각화 layer (canvas/)* 의 일부. 신규 노드 타입 추가 시 본 파일에 행 추가.
 * spec: 62 §4.1 노드 시각적 사양.
 */
import type { NodeTypes } from '@xyflow/react';
import { NodeComponent } from './NodeComponent';

export const nodeTypes: NodeTypes = {
  taskNode: NodeComponent,
  // Future (W4 노드 라이브러리 진입 시):
  //   branchNode: BranchNodeComponent,
  //   joinNode: JoinNodeComponent,
  //   startNode: StartNodeComponent,
  //   endNode: EndNodeComponent,
};
