import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface ChatPanelState {
  isOpen: boolean;
  width: number; // 픽셀 단위
}

const initialState: ChatPanelState = {
  isOpen: false,
  width: 400, // 기본 너비 400px
};

const chatPanelSlice = createSlice({
  name: 'chatPanel',
  initialState,
  reducers: {
    toggleChatPanel: (state) => {
      state.isOpen = !state.isOpen;
    },
    openChatPanel: (state) => {
      state.isOpen = true;
    },
    closeChatPanel: (state) => {
      state.isOpen = false;
    },
    setChatPanelWidth: (state, action: PayloadAction<number>) => {
      // 최소 300px, 최대 600px
      state.width = Math.min(600, Math.max(300, action.payload));
    },
  },
});

export const { toggleChatPanel, openChatPanel, closeChatPanel, setChatPanelWidth } = chatPanelSlice.actions;
export default chatPanelSlice.reducer;