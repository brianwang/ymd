/**
 * 测试图片资源清单（统一从 /static/testdata/* 引用）
 *
 * 说明：
 * - uni-app 中以 `/static/...` 形式引用静态资源，最终会映射到构建产物的 static 目录。
 * - 这里集中管理页面里用到的“测试/占位”图片，避免各处硬编码路径。
 */
export const TESTDATA_IMAGES = {
  // placeholder
  avatarV2: '/static/testdata/avatar-v2.png',
  coverColivingV2: '/static/testdata/cover-coliving-v2.png',
  coverEventsV2: '/static/testdata/cover-events-v2.png',
  posterBgV2: '/static/testdata/poster-bg-v2.png',

  // empty state
  emptyErrorV2: '/static/testdata/empty-error-v2.png',
  emptyListV2: '/static/testdata/empty-list-v2.png',

  // banners
  bannerV2_1: '/static/testdata/banner-v2-1.png',
  bannerV2_2: '/static/testdata/banner-v2-2.png',
  bannerV2_3: '/static/testdata/banner-v2-3.png',

  // misc
  logo: '/static/testdata/logo.png',
} as const;

export type TestdataImageKey = keyof typeof TESTDATA_IMAGES;
export type TestdataImagePath = (typeof TESTDATA_IMAGES)[TestdataImageKey];

