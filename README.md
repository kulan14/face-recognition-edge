项目名称

基于 Docker 与 Kubernetes 的人脸检测服务部署实验

项目说明

本项目基于 MediaPipe 实现人脸检测功能，并将算法封装为 HTTP 服务。
通过 Docker 容器化与 Kubernetes（Minikube）部署，完成边缘智能应用的工程化运行验证。

功能说明

1.提供人脸检测服务接口

2.支持图像上传并返回人脸数量及位置信息

3.提供服务健康检查接口

接口列表

GET /health

POST /detect

实验环境

OS：Windows 11

Python：3.10

Docker Desktop

Minikube + Kubernetes

项目结构
face-recognition-edge/
├── app.py
├── requirements.txt
├── Dockerfile
├── k8s.yaml
├── test.jpg
└── README.md

实验运行流程
1. 构建 Docker 镜像
docker build -t face-api:1.0 .

2. 启动 Kubernetes 集群
minikube start

3. 加载镜像并部署服务
minikube image load face-api:1.0
kubectl apply -f k8s.yaml

4. 服务访问与测试
kubectl port-forward svc/face-api-svc 8000:8000
curl http://localhost:8000/health
curl -X POST http://localhost:8000/detect -F "image=@test.jpg"

实验结果

服务成功部署至 Kubernetes 集群，并能够正确响应人脸检测请求，返回检测结果数据。

