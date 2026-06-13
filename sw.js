const CACHE_NAME = 'pyscript-offline-v2';
// Danh sách các file cần trình duyệt tự động lưu lại để chạy offline
const ASSETS = [
  './',
  './index.html',
  './index.css',
  './main.py',
  'https://pyscript.net/releases/2024.1.1/core.js',
  'https://pyscript.net/releases/2024.1.1/core.css',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

// Cài đặt và tải các file vào bộ nhớ đệm
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
});

// Kích hoạt cấu hình mới
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
});

// Xử lý khi mất mạng: Nếu có mạng thì lấy file mới, mất mạng thì lấy file trong bộ nhớ đệm ra sài
self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      return cachedResponse || fetch(e.request);
    })
  );
});