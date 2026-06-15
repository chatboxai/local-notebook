# frontend

[English](./README.md)

Vue 3 + TypeScript + Vite 单页应用。生产环境用 Nginx 服务静态文件并反代 `/api` 到 backend。

## 目录

| 路径 | 说明 |
|---|---|
| [src/views/](./src/views) | 页面级组件:`LoginPage` / `HomePage`(项目列表)/ `ProjectPage`(主工作区,左资料 + 中对话)/ `SettingsPage` |
| [src/components/](./src/components) | 可复用 UI:对话气泡、来源面板、Settings 各分组表单等 |
| [src/services/](./src/services) | API 客户端封装(axios) |
| [src/composables/](./src/composables) | Vue 3 composables(状态、流式响应等) |
| [src/router/](./src/router) | Vue Router 路由表 |
| [src/types/](./src/types) | TypeScript 类型定义 |
| [src/utils/](./src/utils) | 工具函数 |
| `vite.config.ts` | Vite 配置(dev 时代理到 backend) |
| `nginx.conf` | 生产 Nginx 配置:`/api/` 反代到 `backend:8000`,`/` 走 Vue Router |

## 与后端的接口约定

- 所有 API 走 `/api` 前缀,Nginx(生产)或 Vite proxy(dev)反代到 backend
- 流式对话用 **SSE**(`text/event-stream`),`proxy_buffering off`
- 鉴权:JWT Bearer Token,登录后存 localStorage,axios interceptor 自动注入

## 本地开发

需要 **Node 20+**。Backend 必须先跑起来(默认 8000)。

```bash
cd frontend
npm install
npm run dev          # 默认 http://localhost:5173
```

Vite dev server 会按 [vite.config.ts](./vite.config.ts) 把 `/api` 代理到 backend。

## 构建

```bash
npm run build        # 输出到 dist/
npm run preview      # 本地预览构建产物
```

Docker 镜像 [Dockerfile](./Dockerfile) 用多阶段构建:Node 阶段 `npm ci && npm run build`,Nginx 阶段托管静态文件。
