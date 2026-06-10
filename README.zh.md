# local-Notebook

[English](./README.md)

> **可完全本地部署的 NotebookLM，专攻非结构化超长文档，代码原生支持多租户扩展。**
>
> 在医疗、法律、金融、合规、科研等无法接受信息错误的场景下，尤其面对动辄数百页的长文档，LLM 的幻觉与细节丢失是绕不过的致命问题。local-Notebook 把每一个回答精确链接到原文位置，人工核验只需一次点击，让 AI 输出从“难以判断真伪”变成“可被快速证伪的结论”。所有数据都可以留在本机或内网。

## 演示

![演示截图](./docs/screenshots/demo.jpg)

> 视频演示后续补充。

## 它解决什么问题

NotebookLM 这类产品验证了“以文档为上下文做信息处理”的基本形态，但有两个问题在实际生产力场景无法绕开：

1. **数据必须上传到外部服务**：法务合同、隐私数据、内部研报等资料往往不可接受。
2. **引用粒度太粗**：文档级引用在长文档核验时仍需要大量人工查找。

local-Notebook 围绕这两点重新设计：

- **完全离网部署**：后端、前端、向量库、文件存储全本地；LLM 也可配置本地模型（Ollama / vLLM 等兼容接口）。
- **Block 级别精确引用**：引用直达原文页码与段落，音频引用可定位到时间戳。
- **架构面向多租户设计**：后端 FastAPI + SQLAlchemy + 任务队列，便于从单机扩展到内网团队或企业租户。
- **LLM Provider 无关**：兼容任意 OpenAI 协议接口，可全私有化或与商业 API 混用。
- **超长文档专项优化**：面向单文档数百页、项目千万字级的长文场景优化切块、跨段引用追踪与检索排序。

## 项目结构

| 目录 | 职责 | 文档 |
|---|---|---|
| [backend/](./backend) | FastAPI 主服务：API 路由、Agent 对话、引用解析、向量检索、ARQ 后台任务 | [backend/README.md](./backend/README.md) |
| [frontend/](./frontend) | Vue 3 + Vite 前端：项目管理、对话界面、Settings 配置、原文跳转 | [frontend/README.md](./frontend/README.md) |
| [services/](./services) | 可选本地模型服务：Embedding / MinerU / FunASR，完全离网时启用 | [services/README.md](./services/README.md) |

## 快速开始

前置要求：Docker Desktop（Mac / Windows）或 Docker Engine + Compose（Linux）。

```bash
git clone https://github.com/<your-org>/local-notebook.git
cd local-notebook
./start.sh up --build
./start.sh up
./start.sh down
./start.sh logs -f
```

启动后访问：

- 前端：[http://localhost:8080](http://localhost:8080)
- 后端 API：[http://localhost:8081](http://localhost:8081)，例如 `curl localhost:8081/health`
- 局域网内其他机器：使用本机 IP + 8080

首次进入后请到 **Settings** 页填入 LLM `api_key` / `base_url`。不用 Docker 的本地开发方式见 [backend/README.md](./backend/README.md) 与 [frontend/README.md](./frontend/README.md)。

## 首次启动较慢是正常的

第一次 `--build` 大约需要 10-25 分钟（国内不挂 mirror 时可能更久）。这是有意的取舍：项目为了离线后的稳定性与能力上限，优先选择了能完全本地运行的依赖（向量库、文档解析、Agent 框架等）。安装完成后，运行时不再依赖外部下载或服务。

### 国内常见问题

- **镜像拉不下来**：报错通常包含 `registry-1.docker.io: Client.Timeout exceeded`，给 Docker Desktop 配置可用 registry mirror 即可。
- **build 时 apt / pip 装包很慢**：可以通过环境变量切换国内源：

```bash
APT_MIRROR=mirrors.aliyun.com \
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple \
./start.sh up -d --build
```

如果镜像源和包源都可用但仍 timeout，大概率是本地代理截断了请求。可临时关闭代理，或在 Docker Desktop → Settings → Resources → Proxies 选择 “No proxy” 排查。

## 配置

启动后到前端 **Settings** 页填入 LLM / Embedding / MinerU / FunASR 配置，实时生效，无需重启。

![配置页截图](./docs/screenshots/setting.jpg)

推荐路径：首次部署先用云 API（阿里云百炼 / OpenAI 兼容服务等）快速跑通流程；之后可在 Settings 页逐项切换到 [services/](./services) 下的本地模型服务（Ollama / vLLM / 本地 Embedding / MinerU / FunASR），实现端到端离网。

> **Embedding 是例外**：Embedding 模型不同会导致向量维度与语义空间不同。切换 Embedding 后，已索引的向量数据全部失效，需要删除项目、重新上传文件并重建索引。建议首次部署时先确定 Embedding 服务，再批量上传文件。

## 数据持久化

所有数据保存在 `LOCAL_NOTEBOOK_DATA_DIR`，默认 `./local-notebook-data/`（启动时自动创建）：

```text
$LOCAL_NOTEBOOK_DATA_DIR/
├── local_notebook.db
├── local_notebook.db-wal
├── etcd/
├── minio/
├── milvus/
└── uploads/
```

自定义路径：

```bash
LOCAL_NOTEBOOK_DATA_DIR=/Users/foo/MyNotebook ./start.sh up
```

备份方式：停止服务后直接 `cp -r` 整个目录。

## 重要提示

- **LLM API key 以明文存 SQLite**：不要把数据目录推到公开仓库。
- **不要指向网络盘**：NAS / iCloud Drive / OneDrive 同步盘可能损坏 SQLite WAL。
- **macOS / Windows 性能**：Docker Desktop bind mount 对大量小文件 IO 有延迟，数千文件时可考虑 named volume。
- **生产部署务必覆盖 `SECRET_KEY`**：`export SECRET_KEY=$(openssl rand -hex 32)`。

## Roadmap

| 阶段 | 主要内容 |
|---|---|
| **v0.1** | 单机本地部署、Block 级引用、多模态来源面 |
| **v0.2** | 右侧产出面板、多模态产出、报告导出、图像与视频生成 |
| **v0.3** | 自动记忆持久化、Skill 库自迭代、长期任务规划 |
| **v0.4+** | 多租户隔离、SSO 登录、审计日志、PostgreSQL + Milvus 集群部署模板 |

## License

[Apache License 2.0](./LICENSE)
