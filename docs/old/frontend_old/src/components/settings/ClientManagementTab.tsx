import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../app/store';
import { Button, Input, Table, EmptyState } from '../common';
import { Plus, Trash2, Link, CheckCircle, XCircle, Settings } from 'lucide-react';
import type { TableColumn } from '../common';

interface Client {
  id: string;
  name: string;
  apiConnections: {
    naver: boolean;
    kakao: boolean;
    google: boolean;
    meta: boolean;
  };
  createdAt: string;
  campaigns: number;
  status: 'active' | 'paused';
}

const mockClients: Client[] = [
  {
    id: '1',
    name: '코스모스 뷰티',
    apiConnections: {
      naver: true,
      kakao: true,
      google: true,
      meta: true,
    },
    createdAt: '2024-01-15',
    campaigns: 7,
    status: 'active',
  },
  {
    id: '2',
    name: '홈플렉스',
    apiConnections: {
      naver: true,
      kakao: false,
      google: true,
      meta: true,
    },
    createdAt: '2024-02-01',
    campaigns: 5,
    status: 'active',
  },
  {
    id: '3',
    name: '스타일워크',
    apiConnections: {
      naver: true,
      kakao: true,
      google: false,
      meta: true,
    },
    createdAt: '2024-02-20',
    campaigns: 8,
    status: 'active',
  },
];

export const ClientManagementTab: React.FC = () => {
  const dispatch = useDispatch();
  const [clients, setClients] = useState<Client[]>(mockClients);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [newClientName, setNewClientName] = useState('');

  const columns: TableColumn<Client>[] = [
    {
      key: 'name',
      label: '클라이언트명',
      render: (value) => (
        <div className="font-medium text-gray-900">{value}</div>
      ),
    },
    {
      key: 'apiConnections',
      label: 'API 연동 상태',
      render: (value) => (
        <div className="flex gap-2">
          {Object.entries(value).map(([platform, connected]) => (
            <span
              key={platform}
              className={`px-2 py-1 text-xs rounded-full ${
                connected
                  ? 'bg-success/10 text-success'
                  : 'bg-gray-100 text-gray-400'
              }`}
            >
              {platform.toUpperCase()}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: 'campaigns',
      label: '캠페인 수',
      align: 'center',
      render: (value) => (
        <span className="text-sm font-medium">{value}개</span>
      ),
    },
    {
      key: 'createdAt',
      label: '생성일',
      render: (value) => (
        <span className="text-sm text-gray-600">{value}</span>
      ),
    },
    {
      key: 'status',
      label: '상태',
      align: 'center',
      render: (value) => (
        <span
          className={`px-2 py-1 text-xs rounded-full ${
            value === 'active'
              ? 'bg-success/10 text-success'
              : 'bg-gray-100 text-gray-600'
          }`}
        >
          {value === 'active' ? '활성' : '일시중지'}
        </span>
      ),
    },
    {
      key: 'actions',
      label: '관리',
      align: 'center',
      render: (_, row) => (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => handleApiSettings(row)}
            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
            title="API 설정"
          >
            <Link className="w-4 h-4 text-gray-600" />
          </button>
          <button
            onClick={() => handleDelete(row.id)}
            className="p-1.5 hover:bg-danger/10 rounded-lg transition-colors"
            title="삭제"
          >
            <Trash2 className="w-4 h-4 text-danger" />
          </button>
        </div>
      ),
    },
  ];

  const handleAddClient = () => {
    if (!newClientName.trim()) return;

    const newClient: Client = {
      id: Date.now().toString(),
      name: newClientName,
      apiConnections: {
        naver: false,
        kakao: false,
        google: false,
        meta: false,
      },
      createdAt: new Date().toISOString().split('T')[0],
      campaigns: 0,
      status: 'active',
    };

    setClients([...clients, newClient]);
    setNewClientName('');
    setShowAddModal(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('정말 이 클라이언트를 삭제하시겠습니까? 관련된 모든 데이터가 삭제됩니다.')) {
      setClients(clients.filter(c => c.id !== id));
    }
  };

  const handleApiSettings = (client: Client) => {
    setSelectedClient(client);
    // API 설정 모달 열기
  };

  return (
    <div>
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">클라이언트 관리</h2>
            <p className="text-sm text-gray-600 mt-1">
              클라이언트를 추가하고 광고 플랫폼 API를 연동합니다
            </p>
          </div>
          <Button
            variant="primary"
            onClick={() => setShowAddModal(true)}
          >
            <Plus className="w-4 h-4" />
            클라이언트 추가
          </Button>
        </div>
      </div>

      {clients.length === 0 ? (
        <EmptyState
          title="클라이언트가 없습니다"
          description="첫 번째 클라이언트를 추가하여 광고 관리를 시작하세요"
          action={{
            label: '클라이언트 추가',
            onClick: () => setShowAddModal(true),
          }}
        />
      ) : (
        <Table
          columns={columns}
          data={clients}
          className="bg-white"
        />
      )}

      {/* 클라이언트 추가 모달 */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">새 클라이언트 추가</h3>

            <Input
              label="클라이언트명"
              value={newClientName}
              onChange={(e) => setNewClientName(e.target.value)}
              placeholder="예: 코스모스 뷰티"
              fullWidth
            />

            <div className="bg-info-bg rounded-lg p-3 mt-4">
              <p className="text-sm text-gray-600">
                클라이언트를 추가한 후 광고 플랫폼 API를 연동할 수 있습니다.
              </p>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button
                variant="ghost"
                onClick={() => {
                  setShowAddModal(false);
                  setNewClientName('');
                }}
              >
                취소
              </Button>
              <Button
                variant="primary"
                onClick={handleAddClient}
                disabled={!newClientName.trim()}
              >
                추가
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* API 설정 모달 */}
      {selectedClient && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {selectedClient.name} - API 연동 설정
            </h3>

            <div className="space-y-4">
              {Object.entries(selectedClient.apiConnections).map(([platform, connected]) => (
                <div key={platform} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-semibold capitalize">
                        {platform === 'naver' ? '네이버 광고' :
                         platform === 'kakao' ? '카카오 모먼트' :
                         platform === 'google' ? '구글 애즈' :
                         '메타 광고'}
                      </span>
                      {connected ? (
                        <span className="flex items-center gap-1 text-xs text-success">
                          <CheckCircle className="w-3.5 h-3.5" />
                          연동됨
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-gray-400">
                          <XCircle className="w-3.5 h-3.5" />
                          미연동
                        </span>
                      )}
                    </div>
                    <Button
                      variant={connected ? 'ghost' : 'primary'}
                      size="sm"
                    >
                      {connected ? '재연동' : '연동하기'}
                    </Button>
                  </div>

                  {connected && (
                    <div className="text-xs text-gray-500">
                      마지막 동기화: 2024.03.20 14:30
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button
                variant="ghost"
                onClick={() => setSelectedClient(null)}
              >
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};