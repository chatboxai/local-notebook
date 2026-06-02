#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

DELETE_DATA=false

for arg in "$@"; do
  case "$arg" in
    -d|--data)
      DELETE_DATA=true
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./clean.sh [--data]

清理 local-Notebook 运行产生的中间文件。

Options:
  -d, --data     除中间文件外,同时删除数据目录
                 (LOCAL_NOTEBOOK_DATA_DIR,默认 ./local-notebook-data)
                 包括 SQLite 数据库、向量库、上传文件、Settings 表中的
                 LLM API key(明文)。需要输入 yes 二次确认,不可恢复。
  -h, --help     显示此帮助。

Examples:
  ./clean.sh              # 只清理中间文件(安全,可随时使用)
  ./clean.sh --data       # 清理中间文件并删除全部数据(需确认)

提示:清理前建议先 ./start.sh down 停止服务,避免占用导致删除失败。
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Run './clean.sh --help' for usage." >&2
      exit 1
      ;;
  esac
done

# ────────────────────────────────────────────────────────────────
# 前置检查:docker compose 是否在运行
# ────────────────────────────────────────────────────────────────
DOCKER_RUNNING=false
if command -v docker >/dev/null 2>&1; then
  if [[ -n "$(docker compose ps -q 2>/dev/null)" ]]; then
    DOCKER_RUNNING=true
  fi
fi

if [[ "$DOCKER_RUNNING" == "true" ]]; then
  echo "检测到 docker compose 服务正在运行。"
  if [[ "$DELETE_DATA" == "true" ]]; then
    echo "数据清理前必须先停止服务,否则可能导致 SQLite 数据损坏。"
    echo ""
    read -p "现在自动执行 ./start.sh down 停止服务?(yes 继续,其他取消整个清理): " stop_confirm
    if [[ "$stop_confirm" == "yes" ]]; then
      ./start.sh down
      echo ""
    else
      echo "已取消。请手动 ./start.sh down 后再运行本脚本。"
      exit 1
    fi
  else
    echo "(中间文件清理与容器隔离,继续)"
    echo ""
  fi
fi

# ────────────────────────────────────────────────────────────────
# Part 1: 清理中间文件(默认操作,安全)
# ────────────────────────────────────────────────────────────────
echo "=== 清理运行中间文件 ==="

echo "  [frontend] node_modules / dist"
rm -rf frontend/node_modules frontend/dist

echo "  [python]   __pycache__ / *.pyc / *.pyo / *.egg-info / .pytest_cache"
find backend services -type d \
  \( -name __pycache__ -o -name .pytest_cache -o -name "*.egg-info" \) \
  -exec rm -rf {} + 2>/dev/null || true
find backend services -type f \
  \( -name "*.pyc" -o -name "*.pyo" \) \
  -delete 2>/dev/null || true

echo "  [OS]       .DS_Store / Thumbs.db"
find . -type f \( -name ".DS_Store" -o -name "Thumbs.db" \) -delete 2>/dev/null || true

echo "中间文件清理完成。"
echo ""

# ────────────────────────────────────────────────────────────────
# Part 2: 清理数据(需 --data 标志 + yes 确认)
# ────────────────────────────────────────────────────────────────
if [[ "$DELETE_DATA" == "true" ]]; then
  DATA_DIR="${LOCAL_NOTEBOOK_DATA_DIR:-./local-notebook-data}"

  echo "=== 数据清理(危险操作,不可恢复) ==="
  echo ""
  echo "以下内容将被永久删除:"
  echo ""
  echo "  [主数据] $DATA_DIR"
  if [[ -d "$DATA_DIR" ]]; then
    echo "           - SQLite 数据库(用户账号、所有项目、所有对话历史)"
    echo "           - 向量库(所有已索引的文档向量)"
    echo "           - 上传的 PDF / 音频 / 笔记"
    echo "           - Settings 中的 LLM API key 等配置(明文存储)"
  else
    echo "           (不存在,跳过)"
  fi
  echo ""
  echo "  [legacy] backend/*.db / *.db-wal / *.db-shm / milvus_data.db* / uploads/"
  echo "           (旧版本遗留路径,若存在一并删除)"
  echo ""
  echo "强烈建议先备份:"
  echo "  cp -r \"$DATA_DIR\" \"$DATA_DIR.backup.\$(date +%Y%m%d-%H%M%S)\""
  echo ""
  read -p "确认删除请输入 yes(任意其他输入均取消): " confirm

  if [[ "$confirm" == "yes" ]]; then
    rm -rf "$DATA_DIR"
    rm -f backend/*.db backend/*.db-wal backend/*.db-shm 2>/dev/null || true
    rm -f backend/milvus_data.db* 2>/dev/null || true
    rm -rf backend/uploads 2>/dev/null || true
    echo ""
    echo "数据已删除。"
  else
    echo ""
    echo "已取消,数据保留。"
  fi
fi
