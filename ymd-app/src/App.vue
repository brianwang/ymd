<script setup lang="ts">
import { onLaunch } from "@dcloudio/uni-app";

onLaunch((options) => {
  const q: Record<string, any> = (options as any)?.query || {};
  const inviterId = q.inviter_id || q.inviterId;
  if (inviterId) {
    uni.setStorageSync("inviter_id", String(inviterId));
  }
});
</script>
<style></style>
