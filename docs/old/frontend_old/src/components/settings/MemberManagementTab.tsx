import React, { useState } from 'react';
import { Button, Input, Table, EmptyState } from '../common';
import { UserPlus, Mail, Shield, Edit2, Trash2 } from 'lucide-react';
import type { TableColumn } from '../common';

interface Member {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'member';
  assignedClients: string[];
  lastLogin: string;
  status: 'active' | 'pending' | 'inactive';
}

const mockMembers: Member[] = [
  {
    id: '1',
    name: '강지수',
    email: 'jisoo.kang@marketingpro.com',
    role: 'admin',
    assignedClients: ['전체'],
    lastLogin: '2024-03-20 14:30',
    status: 'active',
  },
  {
    id: '2',
    name: '최유진',
    email: 'yujin.choi@marketingpro.com',
    role: 'member',
    assignedClients: ['코스모스 뷰티'],
    lastLogin: '2024-03-20 10:15',
    status: 'active',
  },
  {
    id: '3',
    name: '이서연',
    email: 'seoyeon.lee@marketingpro.com',
    role: 'member',
    assignedClients: ['홈플렉스'],
    lastLogin: '2024-03-20 11:45',
    status: 'active',
  },
  {
    id: '4',
    name: '박민호',
    email: 'minho.park@marketingpro.com',
    role: 'member',
    assignedClients: ['스타일워크'],
    lastLogin: '2024-03-19 18:45',
    status: 'active',
  },
];

export const MemberManagementTab: React.FC = () => {
  const [members, setMembers] = useState<Member[]>(mockMembers);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'admin' | 'member'>('member');
  const [selectedClients, setSelectedClients] = useState<string[]>([]);

  const columns: TableColumn<Member>[] = [
    {
      key: 'name',
      label: '이름',
      render: (value, row) => (
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-accent/10 rounded-full flex items-center justify-center">
            <span className="text-xs font-semibold text-accent">
              {value.charAt(0)}
            </span>
          </div>
          <div>
            <div className="font-medium text-gray-900">{value}</div>
            <div className="text-xs text-gray-500">{row.email}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      label: '권한',
      render: (value) => (
        <div className="flex items-center gap-1">
          {value === 'admin' ? (
            <>
              <Shield className="w-3.5 h-3.5 text-warning" />
              <span className="text-sm font-medium">Admin</span>
            </>
          ) : (
            <span className="text-sm text-gray-600">Member</span>
          )}
        </div>
      ),
    },
    {
      key: 'assignedClients',
      label: '배정 클라이언트',
      render: (value) => (
        <div className="flex flex-wrap gap-1">
          {value.slice(0, 2).map((client: string) => (
            <span
              key={client}
              className="px-2 py-0.5 text-xs bg-gray-100 rounded-full"
            >
              {client}
            </span>
          ))}
          {value.length > 2 && (
            <span className="px-2 py-0.5 text-xs bg-gray-100 rounded-full">
              +{value.length - 2}
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'lastLogin',
      label: '마지막 로그인',
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
              : value === 'pending'
              ? 'bg-warning/10 text-warning'
              : 'bg-gray-100 text-gray-600'
          }`}
        >
          {value === 'active' ? '활성' : value === 'pending' ? '초대 대기' : '비활성'}
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
            onClick={() => handleEdit(row)}
            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
            title="수정"
          >
            <Edit2 className="w-4 h-4 text-gray-600" />
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

  const handleInvite = () => {
    if (!inviteEmail.trim()) return;

    const newMember: Member = {
      id: Date.now().toString(),
      name: inviteEmail.split('@')[0],
      email: inviteEmail,
      role: inviteRole,
      assignedClients: selectedClients,
      lastLogin: '-',
      status: 'pending',
    };

    setMembers([...members, newMember]);
    setInviteEmail('');
    setSelectedClients([]);
    setShowInviteModal(false);

    alert(`${inviteEmail}로 초대 이메일을 발송했습니다.`);
  };

  const handleEdit = (member: Member) => {
    // 수정 모달 열기
    console.log('Edit member:', member);
  };

  const handleDelete = (id: string) => {
    if (confirm('정말 이 멤버를 삭제하시겠습니까?')) {
      setMembers(members.filter(m => m.id !== id));
    }
  };

  return (
    <div>
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">멤버 관리</h2>
            <p className="text-sm text-gray-600 mt-1">
              팀 멤버를 초대하고 권한을 관리합니다
            </p>
          </div>
          <Button
            variant="primary"
            onClick={() => setShowInviteModal(true)}
          >
            <UserPlus className="w-4 h-4" />
            멤버 초대
          </Button>
        </div>
      </div>

      <div className="bg-white rounded-lg">
        <Table
          columns={columns}
          data={members}
        />
      </div>

      {/* 멤버 초대 모달 */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">멤버 초대</h3>

            <div className="space-y-4">
              <Input
                label="이메일 주소"
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="member@company.com"
                fullWidth
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  권한 설정
                </label>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="role"
                      value="admin"
                      checked={inviteRole === 'admin'}
                      onChange={() => setInviteRole('admin')}
                      className="text-accent"
                    />
                    <div>
                      <div className="font-medium flex items-center gap-1">
                        <Shield className="w-3.5 h-3.5 text-warning" />
                        Admin
                      </div>
                      <p className="text-xs text-gray-500">
                        클라이언트 추가/삭제, 멤버 초대, 설정 관리 가능
                      </p>
                    </div>
                  </label>
                  <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="role"
                      value="member"
                      checked={inviteRole === 'member'}
                      onChange={() => setInviteRole('member')}
                      className="text-accent"
                    />
                    <div>
                      <div className="font-medium">Member</div>
                      <p className="text-xs text-gray-500">
                        배정된 클라이언트만 접근 가능
                      </p>
                    </div>
                  </label>
                </div>
              </div>

              {inviteRole === 'member' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    클라이언트 배정
                  </label>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {['코스모스 뷰티', '홈플렉스', '스타일워크'].map(client => (
                      <label key={client} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          value={client}
                          checked={selectedClients.includes(client)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedClients([...selectedClients, client]);
                            } else {
                              setSelectedClients(selectedClients.filter(c => c !== client));
                            }
                          }}
                          className="text-accent"
                        />
                        <span className="text-sm">{client}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 mt-4 p-3 bg-info-bg rounded-lg">
              <Mail className="w-4 h-4 text-accent flex-shrink-0" />
              <p className="text-xs text-gray-600">
                초대 이메일이 발송됩니다. 수락 후 24시간 내에 가입을 완료해야 합니다.
              </p>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button
                variant="ghost"
                onClick={() => {
                  setShowInviteModal(false);
                  setInviteEmail('');
                  setSelectedClients([]);
                }}
              >
                취소
              </Button>
              <Button
                variant="primary"
                onClick={handleInvite}
                disabled={!inviteEmail.trim()}
              >
                초대하기
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};