export const BASE_URL = 'http://localhost:8000/api/v1';

export const request = (options: UniApp.RequestOptions) => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        Authorization: uni.getStorageSync('token')
          ? `Bearer ${uni.getStorageSync('token')}`
          : '',
        ...options.header,
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else if (res.statusCode === 401 || res.statusCode === 403) {
          uni.showToast({ title: '认证失败，请重新登录', icon: 'none' });
          uni.removeStorageSync('token');
          reject(res);
        } else {
          uni.showToast({ title: (res.data as any)?.detail || '请求失败', icon: 'none' });
          reject(res);
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络异常', icon: 'none' });
        reject(err);
      },
    });
  });
};
