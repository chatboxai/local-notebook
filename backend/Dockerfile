FROM python:3.12-slim

# 可选的 apt / pip 国内镜像(默认用官方源,海外用户无感)。
# 国内用户网络不稳时可通过环境变量指定:
#   APT_MIRROR=mirrors.ustc.edu.cn PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
#   ./start.sh up --build
ARG APT_MIRROR=""
ARG PIP_INDEX_URL=""

WORKDIR /app

COPY requirements.txt .
# build-essential 用于编译 pip 包的 C 扩展(pymilvus 等),装完即卸,不进运行时。
# Acquire::Retries=5 + timeout=60 让 apt 在网络抖动时自动重试。
RUN if [ -n "$APT_MIRROR" ]; then \
        sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
        sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list 2>/dev/null || true; \
    fi \
    && apt-get update \
    && apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=60 \
        install -y --no-install-recommends build-essential \
    && pip install --no-cache-dir --retries 5 --timeout 60 \
        ${PIP_INDEX_URL:+--index-url $PIP_INDEX_URL} \
        -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . .

ENV REDIS_URL=redis://redis:6379 \
    PORT=8000

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]