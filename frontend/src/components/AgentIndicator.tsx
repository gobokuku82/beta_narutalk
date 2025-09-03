import React from 'react';
import { Box, Chip, Zoom } from '@mui/material';
import {
  Search as SearchIcon,
  Description as DocIcon,
  Gavel as RuleIcon,
  Analytics as ChartIcon,
  Hub as HubIcon,
} from '@mui/icons-material';

interface AgentIndicatorProps {
  agent: string;
}

const AgentIndicator: React.FC<AgentIndicatorProps> = ({ agent }) => {
  const getAgentInfo = () => {
    switch (agent) {
      case 'info_retrieval':
        return {
          label: '정보 검색 중',
          icon: <SearchIcon sx={{ fontSize: 16 }} />,
          color: '#7DD3FC',
        };
      case 'doc_generation':
        return {
          label: '문서 생성 중',
          icon: <DocIcon sx={{ fontSize: 16 }} />,
          color: '#A78BFA',
        };
      case 'compliance':
        return {
          label: '규정 검토 중',
          icon: <RuleIcon sx={{ fontSize: 16 }} />,
          color: '#FB923C',
        };
      case 'analytics':
        return {
          label: '데이터 분석 중',
          icon: <ChartIcon sx={{ fontSize: 16 }} />,
          color: '#10B981',
        };
      case 'supervisor':
        return {
          label: '처리 중',
          icon: <HubIcon sx={{ fontSize: 16 }} />,
          color: '#8B5CF6',
        };
      default:
        return {
          label: agent,
          icon: <HubIcon sx={{ fontSize: 16 }} />,
          color: '#737373',
        };
    }
  };

  const info = getAgentInfo();

  return (
    <Zoom in timeout={300}>
      <Chip
        icon={info.icon}
        label={info.label}
        size="small"
        sx={{
          background: `${info.color}20`,
          color: info.color,
          borderColor: info.color,
          fontWeight: 600,
          '& .MuiChip-icon': {
            color: info.color,
          },
        }}
      />
    </Zoom>
  );
};

export default AgentIndicator;