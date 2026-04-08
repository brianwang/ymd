<template>
  <view class="page">
    <view class="field">
      <textarea
        v-model="content"
        class="textarea"
        placeholder="分享点什么..."
        maxlength="1000"
        auto-height
      />
    </view>

    <view class="imgs">
      <view v-for="(it, idx) in images" :key="it.path" class="img-item">
        <image class="img" :src="it.path" mode="aspectFill" />
        <view class="img-mask" v-if="it.uploading">
          <text class="img-mask-text">上传中</text>
        </view>
        <view class="remove" @click.stop="removeImage(idx)">×</view>
      </view>
      <view v-if="images.length < 9" class="add" @click="pickImages">
        <text class="add-text">+ 添加图片</text>
      </view>
    </view>

    <button class="submit" :loading="submitting" :disabled="submitting" @click="submit">
      发布
    </button>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { BASE_URL, request } from '@/utils/request';

type LocalImage = {
  path: string;
  uploading: boolean;
  url?: string;
};

const content = ref('');
const images = ref<LocalImage[]>([]);
const submitting = ref(false);

const pickImages = () => {
  uni.chooseImage({
    count: 9 - images.value.length,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const paths = (res.tempFilePaths || []) as string[];
      const next = paths.map((p: string) => ({ path: p, uploading: false })) as LocalImage[];
      images.value = images.value.concat(next);
    },
  });
};

const removeImage = (index: number) => {
  images.value.splice(index, 1);
};

const uploadOne = (filePath: string) => {
  return new Promise<string>((resolve, reject) => {
    const token = uni.getStorageSync('token');
    uni.uploadFile({
      url: BASE_URL + '/media/upload',
      filePath,
      name: 'file',
      header: {
        Authorization: token ? `Bearer ${token}` : '',
      },
      success: (res) => {
        try {
          const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
          if (!data?.url) throw new Error('invalid response');
          resolve(data.url);
        } catch (e) {
          reject(e);
        }
      },
      fail: (err) => reject(err),
    });
  });
};

const submit = async () => {
  if (submitting.value) return;
  if (!content.value.trim() && images.value.length === 0) {
    uni.showToast({ title: '请输入内容或选择图片', icon: 'none' });
    return;
  }
  submitting.value = true;
  uni.showLoading({ title: '发布中' });
  try {
    const imageUrls: string[] = [];
    for (const it of images.value) {
      if (it.url) {
        imageUrls.push(it.url);
        continue;
      }
      it.uploading = true;
      const url = await uploadOne(it.path);
      it.url = url;
      it.uploading = false;
      imageUrls.push(url);
    }
    await request({
      url: '/posts',
      method: 'POST',
      data: { content: content.value.trim(), image_urls: imageUrls },
    });
    uni.hideLoading();
    uni.showToast({ title: '发布成功', icon: 'success' });
    setTimeout(() => {
      uni.navigateBack();
    }, 300);
  } catch (e) {
    uni.hideLoading();
  } finally {
    submitting.value = false;
    images.value = images.value.map((it) => ({ ...it, uploading: false }));
  }
};
</script>

<style>
.page {
  padding: 16rpx;
}
.field {
  background: #fff;
  border-radius: 16rpx;
  padding: 16rpx;
}
.textarea {
  width: 100%;
  min-height: 240rpx;
  font-size: 30rpx;
  line-height: 44rpx;
  color: #111;
}
.imgs {
  margin-top: 16rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}
.img-item {
  width: 210rpx;
  height: 210rpx;
  position: relative;
}
.img {
  width: 210rpx;
  height: 210rpx;
  border-radius: 12rpx;
  background: #f2f2f2;
}
.img-mask {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  border-radius: 12rpx;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}
.img-mask-text {
  color: #fff;
  font-size: 24rpx;
}
.remove {
  position: absolute;
  right: 8rpx;
  top: 8rpx;
  width: 40rpx;
  height: 40rpx;
  border-radius: 20rpx;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  text-align: center;
  line-height: 40rpx;
  font-size: 28rpx;
}
.add {
  width: 210rpx;
  height: 210rpx;
  border-radius: 12rpx;
  background: #fff;
  border: 2rpx dashed #ddd;
  display: flex;
  align-items: center;
  justify-content: center;
}
.add-text {
  font-size: 26rpx;
  color: #666;
}
.submit {
  margin-top: 24rpx;
  background: #007aff;
  color: #fff;
}
</style>
