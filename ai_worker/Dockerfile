FROM python:3.11-slim-bookworm

WORKDIR /app/src

ENV DEBIAN_FRONTEND=noninteractive

# Delete the default config and write exactly the 3 HTTPS mirrors we need
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    echo "deb https://mirrors.kernel.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb https://mirrors.kernel.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb https://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    -r requirements.txt
COPY . .

CMD ["python", "-u", "worker.py"]