基于边缘智能的人脸识别应用

项目简介
基于MediaPipe实现的人脸检测系统，支持Docker容器化部署和Kubernetes集群管理。

功能特性
- 实时人脸检测
- 前端可视化界面
- 数据库保存检测记录
- RESTful API接口
- Kubernetes部署支持
- 数据持久化存储

技术栈
- Python 3.10
- Flask + MediaPipe
- SQLite
- Docker
- Kubernetes (Minikube)

快速开始

本地运行
bash
pip install -r requirements.txt
python app.py

Docker运行
bash
docker build -t face-api:1.3 .
docker run -p 8000:8000 face-api:1.3

Kubernetes部署
bash
minikube start
minikube image load face-api:1.3
kubectl apply -f k8s.yaml
kubectl port-forward svc/face-api-svc 8000:8000

API接口
GET /health` - 健康检查
POST /detect` - 人脸检测
GET /records` - 查看历史记录
GET /records/stats` - 统计信息

项目结构
face-recognition-edge/
├── app.py              主应用
├── face_detect.py      本地测试
├── requirements.txt    依赖
├── Dockerfile          Docker配置
├── k8s.yaml            K8s部署配置
├── index.html          前端界面
├── app.js              前端逻辑
└── README.md           项目文档

作者
张泽楷

许可
MIT License
