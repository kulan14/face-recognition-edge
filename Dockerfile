# 使用Python 3.10精简版作为基础镜像
FROM python:3.10-slim

# 安装OpenCV在Linux容器中需要的系统依赖库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 设置容器内的工作目录
WORKDIR /app

# 先复制依赖文件（利用Docker缓存机制，如果requirements.txt没变，这层会被缓存）
COPY requirements.txt .

# 安装Python依赖包
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .

# 创建数据目录用于存储SQLite数据库
RUN mkdir -p /data

# 声明容器对外暴露的端口
EXPOSE 8000

# 设置环境变量，指定数据库文件路径
ENV DB_PATH=/data/face_detection.db

# 容器启动时执行的命令
CMD ["python", "app.py"]