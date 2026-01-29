# -*- coding: utf-8 -*-
"""
本地人脸检测测试脚本
使用摄像头实时检测人脸并标记
"""
import os

# 可选设置：屏蔽 TensorFlow/absl 的部分日志（不影响功能）
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"   # 0=全部日志, 1=INFO以上, 2=WARNING以上, 3=只剩ERROR

import cv2
import mediapipe as mp


def main():
    # MediaPipe Face Detection初始化（只检测人脸位置）
    mp_face_detection = mp.solutions.face_detection
    face_detection = mp_face_detection.FaceDetection(
        model_selection=0,  # 0=短距离模型（2米内），1=长距离模型（5米内）
        min_detection_confidence=0.5  # 最小检测置信度
    )

    # 打开摄像头（0表示默认摄像头）
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    # 创建窗口
    cv2.namedWindow("Face Detection", cv2.WINDOW_NORMAL)

    while True:
        # 读取一帧图像
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        
        # 水平翻转（镜像效果，更符合自拍习惯）
        frame = cv2.flip(frame, 1)
        
        # 获取图像尺寸
        h, w = frame.shape[:2]

        # MediaPipe 需要 RGB 格式
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb)

        # 在原始frame上绘制（不在rgb上，确保显示正常）
        if results.detections:
            for det in results.detections:
                # det.location_data.relative_bounding_box 返回相对坐标（0~1范围）
                box = det.location_data.relative_bounding_box
                
                # 转换为绝对坐标
                x1 = int(box.xmin * w)
                y1 = int(box.ymin * h)
                x2 = int((box.xmin + box.width) * w)
                y2 = int((box.ymin + box.height) * h)

                # 限制边界范围
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w - 1, x2)
                y2 = min(h - 1, y2)

                # 获取置信度分数
                score = det.score[0] if det.score else 0.0
                label = f"{score:.2f}"

                # 绘制矩形框和文字（可以指定颜色，这里为绿色，也可以改为其他颜色）
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, max(0, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 缩放后再显示（这样只影响显示，不影响检测精度）
        show = cv2.resize(frame, (960, 540))
        cv2.imshow("Face Detection", show)

        # 按 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()