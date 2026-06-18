import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { TrendData, TrendKeyword } from '../../types';
import { mockTrendData, emptyTrendData } from '../../constants/mockTrend';

interface TrendState {
  data: TrendData;
  selectedKeywords: string[];
  selectedCategories: string[];
  isLoading: boolean;
  error: string | null;
  dateRange: {
    start: string;
    end: string;
  };
}

const initialState: TrendState = {
  data: emptyTrendData,
  selectedKeywords: [],
  selectedCategories: [],
  isLoading: false,
  error: null,
  dateRange: {
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  }
};

// 트렌드 데이터 가져오기 (비동기 액션)
export const fetchTrendData = createAsyncThunk(
  'trend/fetchData',
  async (clientName: string) => {
    // TODO: 실 API 연동 시 주석 해제 - Naver DataLab, 쇼핑인사이트, YouTube API 통합 엔드포인트
    // const response = await fetch(`/api/trend/data?client=${encodeURIComponent(clientName)}`);
    // const data = await response.json();
    // return data;

    // 목업 데이터 사용 중
    return new Promise<TrendData>((resolve) => {
      setTimeout(() => {
        resolve(mockTrendData[clientName] || emptyTrendData);
      }, 500); // API 호출 시뮬레이션
    });
  }
);

// 키워드 검색량 데이터 추가 가져오기
export const fetchKeywordTrend = createAsyncThunk(
  'trend/fetchKeyword',
  async ({ keyword, clientName }: { keyword: string; clientName: string }) => {
    // TODO: 실 API 연동 시 주석 해제 - Naver DataLab API
    // const response = await fetch('/api/trend/keywords', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ keyword, client: clientName })
    // });
    // const data = await response.json();
    // return data;

    // 목업 데이터 생성
    return new Promise<TrendKeyword>((resolve) => {
      setTimeout(() => {
        const dates = Array.from({ length: 30 }, (_, i) => {
          const date = new Date();
          date.setDate(date.getDate() - (29 - i));
          return date.toISOString().split('T')[0];
        });

        const values = Array.from({ length: 30 }, () =>
          Math.floor(Math.random() * 80) + 20
        );

        resolve({ keyword, values, dates });
      }, 300);
    });
  }
);

const trendSlice = createSlice({
  name: 'trend',
  initialState,
  reducers: {
    toggleKeyword: (state, action: PayloadAction<string>) => {
      const keyword = action.payload;
      const index = state.selectedKeywords.indexOf(keyword);

      if (index > -1) {
        state.selectedKeywords.splice(index, 1);
      } else if (state.selectedKeywords.length < 5) {
        // 최대 5개까지만 선택 가능
        state.selectedKeywords.push(keyword);
      }
    },
    toggleCategory: (state, action: PayloadAction<string>) => {
      const category = action.payload;
      const index = state.selectedCategories.indexOf(category);

      if (index > -1) {
        state.selectedCategories.splice(index, 1);
      } else {
        state.selectedCategories.push(category);
      }
    },
    setDateRange: (state, action: PayloadAction<{ start: string; end: string }>) => {
      state.dateRange = action.payload;
    },
    clearSelections: (state) => {
      state.selectedKeywords = [];
      state.selectedCategories = [];
    }
  },
  extraReducers: (builder) => {
    builder
      // fetchTrendData
      .addCase(fetchTrendData.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTrendData.fulfilled, (state, action) => {
        state.isLoading = false;
        state.data = action.payload;
        // 자동으로 처음 2개 키워드 선택
        if (action.payload.keywords.length > 0) {
          state.selectedKeywords = action.payload.keywords
            .slice(0, 2)
            .map(k => k.keyword);
        }
        // 자동으로 처음 2개 카테고리 선택
        if (action.payload.shoppingCategories.length > 0) {
          state.selectedCategories = action.payload.shoppingCategories
            .slice(0, 2)
            .map(c => c.category);
        }
      })
      .addCase(fetchTrendData.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || '트렌드 데이터를 불러오는데 실패했습니다.';
      })
      // fetchKeywordTrend
      .addCase(fetchKeywordTrend.fulfilled, (state, action) => {
        // 기존 키워드가 없으면 추가
        const existingIndex = state.data.keywords.findIndex(
          k => k.keyword === action.payload.keyword
        );

        if (existingIndex === -1) {
          state.data.keywords.push(action.payload);
        } else {
          state.data.keywords[existingIndex] = action.payload;
        }
      });
  }
});

export const { toggleKeyword, toggleCategory, setDateRange, clearSelections } = trendSlice.actions;

export default trendSlice.reducer;