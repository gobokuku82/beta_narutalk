import { useSelector } from 'react-redux';
import { RootState } from '../app/store';

export type UserRole = 'ae' | 'performance' | 'director' | 'ceo';

export function useRoleView() {
  // Redux store에서 현재 사용자 역할 가져오기
  // 실제로는 auth slice에서 가져와야 하지만, 현재는 목업으로 'director' 사용
  const role = useSelector((state: RootState) =>
    // @ts-ignore - auth slice가 아직 없음
    state.auth?.role || 'director'
  ) as UserRole;

  return {
    // 디렉터/CEO만 MER 지표 볼 수 있음
    showMer: role === 'director' || role === 'ceo',

    // 디렉터/CEO만 LTV 지표 볼 수 있음
    showLtv: role === 'director' || role === 'ceo',

    // AE/퍼포먼스 마케터만 상세 채널 데이터 볼 수 있음
    showDetailChannel: role === 'ae' || role === 'performance',

    // 포트폴리오 뷰는 디렉터/CEO만 접근 가능
    canAccessPortfolio: role === 'director' || role === 'ceo',

    // 현재 역할
    currentRole: role,
  };
}