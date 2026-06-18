import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export type UserRole = 'ae' | 'performance' | 'director' | 'ceo';

interface AuthState {
  role: UserRole;
  user: {
    name: string;
    email: string;
  } | null;
}

const initialState: AuthState = {
  role: 'director', // 기본 역할을 director로 설정
  user: {
    name: '강지수',
    email: 'jisoo.kang@marketingpro.com'
  }
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setRole: (state, action: PayloadAction<UserRole>) => {
      state.role = action.payload;
    },
    setUser: (state, action: PayloadAction<AuthState['user']>) => {
      state.user = action.payload;
    },
    logout: (state) => {
      state.user = null;
      state.role = 'ae';
    }
  }
});

export const { setRole, setUser, logout } = authSlice.actions;
export default authSlice.reducer;