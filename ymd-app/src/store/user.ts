import { defineStore } from 'pinia';
import { ref } from 'vue';

export type PreferredLocation = {
  lat: number;
  lng: number;
  display_name?: string | null;
  city?: string | null;
  source?: 'manual' | 'device' | null;
  updated_at?: string | null;
};

export const useUserStore = defineStore('user', () => {
  const token = ref(uni.getStorageSync('token') || '');
  const userInfo = ref(uni.getStorageSync('userInfo') || null);
  const preferredLocation = ref<PreferredLocation | null>(uni.getStorageSync('preferredLocation') || null);

  const setToken = (newToken: string) => {
    token.value = newToken;
    uni.setStorageSync('token', newToken);
  };

  const setUserInfo = (info: any) => {
    userInfo.value = info;
    uni.setStorageSync('userInfo', info);
    if (info && Object.prototype.hasOwnProperty.call(info, 'preferred_location')) {
      preferredLocation.value = info.preferred_location || null;
      uni.setStorageSync('preferredLocation', preferredLocation.value);
    }
  };

  const setPreferredLocation = (loc: PreferredLocation | null) => {
    preferredLocation.value = loc;
    uni.setStorageSync('preferredLocation', loc);
    if (userInfo.value) {
      userInfo.value = { ...(userInfo.value as any), preferred_location: loc };
      uni.setStorageSync('userInfo', userInfo.value);
    }
  };

  const logout = () => {
    token.value = '';
    userInfo.value = null;
    preferredLocation.value = null;
    uni.removeStorageSync('token');
    uni.removeStorageSync('userInfo');
    uni.removeStorageSync('preferredLocation');
  };

  return {
    token,
    userInfo,
    preferredLocation,
    setToken,
    setUserInfo,
    setPreferredLocation,
    logout,
  };
});
