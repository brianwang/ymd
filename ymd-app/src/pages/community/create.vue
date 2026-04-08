<template>
  <view class="ymd-page">
    <AppBar title="发帖" back />
    <view class="ymd-container ymd-page-inner">
      <Card class="field">
        <textarea
          v-model="content"
          class="textarea"
          placeholder="分享点什么..."
          maxlength="1000"
          auto-height
        />
      </Card>

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

      <button class="submit ymd-btn" :loading="submitting" :disabled="submitting" @click="submit">发布</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { BASE_URL, ensureLoggedIn, request } from '@/utils/request';
import AppBar from '@/components/ui/AppBar.vue';
import Card from '@/components/ui/Card.vue';

type LocalImage = {
  path: string;
  uploading: boolean;
  url?: string;
};

const content = ref('');
const images = ref<LocalImage[]>([]);
const submitting = ref(false);

const pickImages = () => {
  if (!ensureLoggedIn()) return;
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
  if (!ensureLoggedIn()) return;
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

<style lang="scss">
.field {
  padding: 12px;
}
.textarea {
  width: 100%;
  min-height: 140px;
  font-size: 15px;
  line-height: 22px;
  color: $ymd-v2-color-text;
}
.imgs {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.img-item {
  width: 104px;
  height: 104px;
  position: relative;
}
.img {
  width: 104px;
  height: 104px;
  border-radius: $ymd-v2-radius-md;
  background: rgba(15, 23, 42, 0.04);
}
.img-mask {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  border-radius: $ymd-v2-radius-md;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}
.img-mask-text {
  color: #fff;
  font-size: 12px;
}
.remove {
  position: absolute;
  right: 6px;
  top: 6px;
  width: 22px;
  height: 22px;
  border-radius: 11px;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  text-align: center;
  line-height: 22px;
  font-size: 16px;
}
.add {
  width: 104px;
  height: 104px;
  border-radius: $ymd-v2-radius-md;
  background: rgba(255, 255, 255, 0.92);
  border: 1px dashed rgba(15, 23, 42, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
}
.add-text {
  font-size: 12px;
  color: $ymd-v2-color-muted;
  font-weight: 800;
}
.submit {
  margin-top: 16px;
  height: 44px;
  line-height: 44px;
  font-weight: 800;
}
</style>
