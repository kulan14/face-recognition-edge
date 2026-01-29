# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import mediapipe as mp
import sqlite3
from datetime import datetime
import os
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 数据库路径配置
DB_PATH = os.getenv("DB_PATH", "/data/face_detection.db")

# MediaPipe 人脸检测
mp_face_detection = mp.solutions.face_detection
detector = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)


def init_db():
    """初始化数据库表"""
    # 确保数据目录存在
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detection_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            face_count INTEGER NOT NULL,
            faces_data TEXT,
            image_width INTEGER,
            image_height INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    print(f"数据库初始化完成: {DB_PATH}")


def save_detection_record(face_count, faces_data, img_width, img_height):
    """保存检测记录到数据库"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 将faces_data转换为JSON字符串存储
        faces_json = json.dumps(faces_data)
        
        cursor.execute('''
            INSERT INTO detection_records (timestamp, face_count, faces_data, image_width, image_height)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, face_count, faces_json, img_width, img_height))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    except Exception as e:
        print(f"保存记录失败: {e}")
        return None


@app.route("/health")
def health():
    """健康检查接口"""
    return "ok"


@app.route("/detect", methods=["POST"])
def detect():
    """人脸检测接口"""
    if "image" not in request.files:
        return jsonify({"error": "missing form-data field: image"}), 400

    file = request.files["image"]
    data = np.frombuffer(file.read(), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"error": "bad image"}), 400

    h, w = img.shape[:2]
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = detector.process(rgb)

    faces = []
    if results.detections:
        for det in results.detections:
            box = det.location_data.relative_bounding_box
            x1 = int(box.xmin * w)
            y1 = int(box.ymin * h)
            x2 = int((box.xmin + box.width) * w)
            y2 = int((box.ymin + box.height) * h)
            score = float(det.score[0]) if det.score else 0.0
            faces.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "score": score})

    # 保存检测记录到数据库
    record_id = save_detection_record(len(faces), faces, w, h)

    return jsonify({
        "faces": faces, 
        "count": len(faces),
        "record_id": record_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/records", methods=["GET"])
def get_records():
    """获取检测记录列表"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取查询参数
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)
        
        cursor.execute('''
            SELECT id, timestamp, face_count, faces_data, image_width, image_height
            FROM detection_records
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                "id": row[0],
                "timestamp": row[1],
                "face_count": row[2],
                "faces": json.loads(row[3]) if row[3] else [],
                "image_width": row[4],
                "image_height": row[5]
            })
        
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM detection_records')
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "records": records,
            "total": total,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/records/<int:record_id>", methods=["GET"])
def get_record(record_id):
    """获取单条记录详情"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, timestamp, face_count, faces_data, image_width, image_height
            FROM detection_records
            WHERE id = ?
        ''', (record_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return jsonify({"error": "Record not found"}), 404
        
        record = {
            "id": row[0],
            "timestamp": row[1],
            "face_count": row[2],
            "faces": json.loads(row[3]) if row[3] else [],
            "image_width": row[4],
            "image_height": row[5]
        }
        
        return jsonify(record)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/records/stats", methods=["GET"])
def get_stats():
    """获取统计信息"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 总记录数
        cursor.execute('SELECT COUNT(*) FROM detection_records')
        total_records = cursor.fetchone()[0]
        
        # 总检测人脸数
        cursor.execute('SELECT SUM(face_count) FROM detection_records')
        total_faces = cursor.fetchone()[0] or 0
        
        # 平均每次检测的人脸数
        cursor.execute('SELECT AVG(face_count) FROM detection_records')
        avg_faces = cursor.fetchone()[0] or 0
        
        # 最近一次检测时间
        cursor.execute('SELECT timestamp FROM detection_records ORDER BY id DESC LIMIT 1')
        last_detection = cursor.fetchone()
        last_detection_time = last_detection[0] if last_detection else None
        
        conn.close()
        
        return jsonify({
            "total_records": total_records,
            "total_faces_detected": total_faces,
            "average_faces_per_detection": round(avg_faces, 2),
            "last_detection_time": last_detection_time
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # 启动时初始化数据库
    init_db()
    app.run(host="0.0.0.0", port=8000)