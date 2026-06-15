const CACHE_NAME = "gcp-management-offline-v4"; // Đổi version để ép trình duyệt xóa cache cũ hoàn toàn
const ASSETS = [
  "https://pyscript.net/releases/2024.1.1/core.js",
  "https://pyscript.net/releases/2024.1.1/core.css",
  "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
  "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }),
  );
  self.skipWaiting(); // Ép kích hoạt Service Worker mới ngay lập tức
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        }),
      );
    }),
  );
  return self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  // Nếu là file giao diện hoặc file code Python nội bộ, bắt buộc đọc trực tiếp từ disk, không dùng cache offline để tránh lỗi lưu giữ code cũ
  if (e.request.url.includes("index.html") || e.request.url.includes("main.py") || e.request.url.includes("index.css") || e.request.url.endsWith("/")) {
    return fetch(e.request);
  }
  
  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      return cachedResponse || fetch(e.request);
    }),
  );
});