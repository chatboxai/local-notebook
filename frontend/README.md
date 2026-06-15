# frontend

[中文](./README.zh.md)

Vue 3 + TypeScript + Vite single-page application. In production, Nginx serves static files and proxies `/api` to the backend.

## Directory

| Path | Description |
|---|---|
| [src/views/](./src/views) | Page-level components: `LoginPage`, `HomePage` for project lists, `ProjectPage` as the main workspace, and `SettingsPage` |
| [src/components/](./src/components) | Reusable UI: chat bubbles, source panels, Settings section forms, and related widgets |
| [src/services/](./src/services) | API client wrappers based on axios |
| [src/composables/](./src/composables) | Vue 3 composables for state and streaming responses |
| [src/router/](./src/router) | Vue Router routes |
| [src/types/](./src/types) | TypeScript type definitions |
| [src/utils/](./src/utils) | Utility functions |
| `vite.config.ts` | Vite configuration, including the dev proxy to the backend |
| `nginx.conf` | Production Nginx config: `/api/` proxies to `backend:8000`, `/` serves the Vue Router app |

## Backend Contract

- All APIs use the `/api` prefix and are proxied to the backend by Nginx in production or the Vite proxy in development.
- Streaming chat uses **SSE** (`text/event-stream`) with `proxy_buffering off`.
- Authentication uses JWT Bearer tokens. After login, the token is stored in localStorage and injected by the axios interceptor.

## Local Development

Requires **Node 20+**. The backend must already be running, defaulting to port `8000`.

```bash
cd frontend
npm install
npm run dev          # default: http://localhost:5173
```

The Vite dev server proxies `/api` to the backend according to [vite.config.ts](./vite.config.ts).

## Build

```bash
npm run build        # output: dist/
npm run preview      # preview the production build locally
```

The Docker image in [Dockerfile](./Dockerfile) uses a multi-stage build: the Node stage runs `npm ci && npm run build`, and the Nginx stage serves the static files.
