import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../app/store';
import { Badge } from '../common/Badge';
import { ProgressBar } from '../common/ProgressBar';

const channelNames = {
  naver: '네이버',
  kakao: '카카오',
  meta: '메타',
  google: '구글',
};

export const ChannelTable: React.FC = () => {
  const clientData = useSelector((state: RootState) => state.client.currentClientData);
  const channels = clientData?.channels || [];

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold">매체별 현황</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">매체</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">상태</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">광고비</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">ROAS</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">CTR</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">CVR</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">CPA</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">예산소진율</th>
            </tr>
          </thead>
          <tbody>
            {channels.map(channel => (
              <tr key={channel.channel} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-6 py-4">
                  <span className="font-medium">{channelNames[channel.channel]}</span>
                </td>
                <td className="px-6 py-4">
                  <Badge
                    variant={
                      channel.status === 'safe' ? 'success' :
                      channel.status === 'warning' ? 'warning' : 'danger'
                    }
                  >
                    {channel.status === 'safe' ? '정상' :
                     channel.status === 'warning' ? '주의' : '위험'}
                  </Badge>
                </td>
                <td className="px-6 py-4 text-right">
                  ₩{channel.spend.toLocaleString()}
                </td>
                <td className="px-6 py-4 text-right">
                  <span className={
                    channel.roas < 300 ? 'text-danger font-semibold' :
                    channel.roas > 400 ? 'text-success font-semibold' : ''
                  }>
                    {channel.roas}%
                  </span>
                </td>
                <td className="px-6 py-4 text-right">{channel.ctr}%</td>
                <td className="px-6 py-4 text-right">{channel.cvr}%</td>
                <td className="px-6 py-4 text-right">₩{channel.cpa.toLocaleString()}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-24">
                      <ProgressBar
                        value={channel.budgetRate}
                        color={channel.budgetRate >= 85 ? 'amber' : 'blue'}
                        height="sm"
                      />
                    </div>
                    <span className="text-sm text-gray-600">{channel.budgetRate}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};