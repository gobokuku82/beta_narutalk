import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../app/store';
import { AlertItem } from '../common/AlertItem';
import { useNavigate } from 'react-router-dom';

export const AiInsightPanel: React.FC = () => {
  const clientData = useSelector((state: RootState) => state.client.currentClientData);
  const insights = clientData?.insights || [];
  const navigate = useNavigate();

  const handleInsightClick = (type: string) => {
    if (type === 'danger' || type === 'warning') {
      navigate('/analysis');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold">AI 인사이트 & 이상 알림</h3>
      </div>
      <div className="p-6 space-y-3">
        {insights.map((insight, index) => (
          <AlertItem
            key={index}
            type={insight.type}
            title={insight.title}
            description={insight.description}
            onClick={() => handleInsightClick(insight.type)}
          />
        ))}
      </div>
    </div>
  );
};