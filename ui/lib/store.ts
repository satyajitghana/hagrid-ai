import { create } from 'zustand';

type Tab = 'analysis' | 'market' | 'positions' | 'funds' | 'news' | 'staging';

interface AppState {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
  selectedDate: string;
  setSelectedDate: (date: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  activeTab: 'analysis',
  setActiveTab: (tab) => set({ activeTab: tab }),
  selectedDate: new Date().toISOString().split('T')[0],
  setSelectedDate: (date) => set({ selectedDate: date }),
}));