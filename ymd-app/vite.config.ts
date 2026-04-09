import { defineConfig, loadEnv } from "vite";
import uni from "@dcloudio/vite-plugin-uni";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiBaseUrl = env.VITE_API_BASE_URL || process.env.VITE_API_BASE_URL || "";

  return {
    plugins: [uni()],
    define: {
      __YMD_API_BASE_URL__: JSON.stringify(apiBaseUrl),
    },
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: '@import "@/styles/tokens.scss";',
        },
      },
    },
  };
});
