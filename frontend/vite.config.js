import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // 개발 중에는 프론트(5173)와 백엔드(8000)가 따로 돈다.
  // /api 로 시작하는 요청만 백엔드로 넘겨서 CORS 를 피한다.
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  // 빌드 결과를 백엔드가 그대로 내려줄 수 있는 위치에 둔다.
  build: {
    outDir: "../backend/static",
    emptyOutDir: true,
  },
});
