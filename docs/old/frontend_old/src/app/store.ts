import { configureStore } from '@reduxjs/toolkit';
import campaignReducer from '../features/campaign/campaignSlice';
import channelReducer from '../features/channel/channelSlice';
import creativeReducer from '../features/creative/creativeSlice';
import hitlReducer from '../features/hitl/hitlSlice';
import portfolioReducer from '../features/portfolio/portfolioSlice';
import agentChatReducer from '../features/agentChat/agentChatSlice';
import authReducer from '../features/auth/authSlice';
import costReducer from '../features/cost/costSlice';
import reportReducer from '../features/report/reportSlice';
import clientReducer from '../features/client/clientSlice';
import chatPanelReducer from '../features/chatPanel/chatPanelSlice';
import navigationReducer from '../features/navigation/navigationSlice';
import settingsReducer from '../features/settings/settingsSlice';
import trendReducer from '../features/trend/trendSlice';

export const store = configureStore({
  reducer: {
    campaign: campaignReducer,
    channel: channelReducer,
    creative: creativeReducer,
    hitl: hitlReducer,
    portfolio: portfolioReducer,
    agentChat: agentChatReducer,
    auth: authReducer,
    cost: costReducer,
    report: reportReducer,
    client: clientReducer,
    chatPanel: chatPanelReducer,
    navigation: navigationReducer,
    settings: settingsReducer,
    trend: trendReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
