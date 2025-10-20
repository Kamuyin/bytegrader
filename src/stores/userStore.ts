import { create } from 'zustand';
import { apiService } from '../services/api';

interface UserInfo {
  first_name: string;
  last_name: string;
  username: string;
  is_admin: boolean;
}

interface UserState {
  userInfo: UserInfo | null;
  loading: boolean;
  fetchUserInfo: () => Promise<void>;
  reset: () => void;
}

const initialState = {
  userInfo: null,
  loading: false
};

export const useUserStore = create<UserState>((set) => ({
  ...initialState,

  fetchUserInfo: async () => {
    set({ loading: true });
    try {
      const response = await apiService.auth.whoami();
      if (!response.success) {
        throw new Error(response.error || 'Failed to fetch user info');
      }
      set({ userInfo: response.data, loading: false });
    } catch (err) {
      set({ loading: false });
      throw err;
    }
  },

  reset: () => set(initialState)
}));
