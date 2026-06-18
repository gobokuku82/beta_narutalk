import { createSlice } from '@reduxjs/toolkit';

// 이제 campaign slice는 client slice에서 데이터를 가져오므로 로컬 상태는 필요 없음
interface CampaignState {
  // 추가적인 캠페인 관련 상태만 관리
}

const initialState: CampaignState = {
};

const campaignSlice = createSlice({
  name: 'campaign',
  initialState,
  reducers: {
    // 필요한 추가 리듀서
  },
});

export default campaignSlice.reducer;