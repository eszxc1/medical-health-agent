# ===== Frontend（Vue 2 + Webpack 3）多阶段构建 =====

# ---------- 阶段 1：构建（Node + Webpack） ----------
FROM node:18-alpine AS builder

WORKDIR /app

# 先复制 package.json，利用 Docker 层缓存加速安装
COPY package.json ./
RUN npm install

# 复制其余代码
COPY . .

# Vue2 + Webpack3 在 Node 17+ 需要 legacy provider（md4 hash / OpenSSL 3 兼容）
ENV NODE_OPTIONS=--openssl-legacy-provider

# 生产构建，产物输出到 dist/
RUN npm run build

# ---------- 阶段 2：运行时（Nginx 静态服务） ----------
FROM nginx:alpine

# 构建产物复制到 Nginx 默认静态目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 内联生成 Nginx 配置（SPA try_files；单引号防止 $uri 被 shell 展开）
RUN printf '%s\n' \
    'server {' \
    '    listen 8080;' \
    '    server_name _;' \
    '    root /usr/share/nginx/html;' \
    '    index index.html;' \
    '    location / { try_files $uri $uri/ /index.html; }' \
    '    location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot|map)$ {' \
    '        expires 7d;' \
    '        add_header Cache-Control "public, max-age=604800";' \
    '    }' \
    '}' \
    > /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
