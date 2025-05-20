import cv2
import threading
import time
import numpy as np
from flask import Flask, Response, render_template, jsonify
from ultralytics import YOLO
import logging
from datetime import datetime
from collections import deque
import requests
from configs.config import Config_AICV

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VideoSurveillancePro')

app = Flask(__name__)

# 初始化模型
try:
    logger.info(f"使用计算设备: {Config_AICV.DEVICE}")
    if Config_AICV.DEVICE == 'cuda':
        detector = YOLO(f'weights/{Config_AICV.MODEL}').half().to(Config_AICV.DEVICE)
    else:
        detector = YOLO(f'weights/{Config_AICV.MODEL}').to(Config_AICV.DEVICE)
    logger.info(f"成功加载模型: {Config_AICV.MODEL}")
except Exception as e:
    logger.error(f"模型加载失败: {str(e)}")
    exit(1)


class CameraProcessor:
    def __init__(self, source, cam_id):
        self.cam_id = cam_id
        self.cam_name = Config_AICV.CAMERAS.get(cam_id, f"Camera_{cam_id}")
        self.cap = None
        self.frame = np.zeros((Config_AICV.DISPLAY_SIZE[1], Config_AICV.DISPLAY_SIZE[0], 3), dtype=np.uint8)
        self.frame_lock = threading.Lock()
        self.active = True
        self.last_update = time.time()
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        self.status = "初始化中"
        self.retry_count = 0
        self.max_retries = 5
        self.detection_history = deque(maxlen=100)
        self.last_detection = []
        # 新增警报相关属性
        self.last_target_alert = 0  # 最后警报时间

        self.thread = threading.Thread(target=self.process_stream, daemon=True)
        self.thread.start()
        logger.info(f"摄像头 {self.cam_id} ({self.cam_name}) 处理器启动")

    def _init_camera(self):
        try:
            cap = cv2.VideoCapture(self.cam_id, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, Config_AICV.BUFFER_SIZE)
            cap.set(cv2.CAP_PROP_FPS, Config_AICV.FPS)

            if not cap.isOpened():
                raise RuntimeError("摄像头未就绪")

            for _ in range(5):
                ret, _ = cap.read()
                if ret:
                    self.status = "运行中"
                    self.retry_count = 0
                    return cap
                time.sleep(0.1)

            raise RuntimeError("无法获取视频帧")

        except Exception as e:
            if self.cap:
                self.cap.release()
            self.status = f"初始化失败: {str(e)}"
            raise

    def process_stream(self):
        while self.active and self.retry_count < self.max_retries:
            try:
                if self.cap is None or not self.cap.isOpened():
                    self.cap = self._init_camera()

                start_time = time.time()
                ret, frame = self.cap.read()

                if not ret:
                    logger.warning(f"摄像头 {self.cam_id} 读取失败，尝试重连...")
                    self.reconnect()
                    continue

                target_detected = False
                current_detection = []
                processed_frame = None  # 用于保存处理后的帧

                if Config_AICV.DEVICE == 'cuda':
                    # 转换颜色空间为RGB进行推理
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = detector.predict(
                        frame_rgb,
                        imgsz=640,
                        half=True,
                        device=Config_AICV.DEVICE,
                        verbose=False,
                        stream=False
                    )
                    # 获取绘制后的RGB图像
                    processed_frame_rgb = results[0].plot()
                    # 转换回BGR用于编码和显示
                    processed_frame = cv2.cvtColor(processed_frame_rgb, cv2.COLOR_RGB2BGR)
                else:
                    results = detector.predict(
                        frame,
                        imgsz=640,
                        device='cpu',
                        verbose=False
                    )
                    processed_frame = results[0].plot()  # CPU模式下直接使用BGR格式

                # 调整帧尺寸
                resized = cv2.resize(processed_frame, Config_AICV.DISPLAY_SIZE)

                # 手机检测处理
                current_time = time.time()
                for box in results[0].boxes:
                    class_id = int(box.cls)
                    class_name = detector.names[class_id]
                    conf = float(box.conf)
                    current_detection.append({
                        "class": class_name,
                        "confidence": conf,
                        "timestamp": time.time()
                    })

                    if (Config_AICV.CLASS_BOX_NAME.__contains__(class_name) and
                            conf >= Config_AICV.TARGET_CONFIDENCE):
                        target_detected = True

                # 触发警报（使用处理后的BGR帧）
                if target_detected and (current_time - self.last_target_alert) > Config_AICV.ALERT_COOLDOWN:
                    # 使用原始分辨率帧（processed_frame）
                    self._send_phone_alert(processed_frame)
                    self.last_target_alert = current_time

                # 记录检测结果
                self.last_detection = current_detection
                self.detection_history.extend(current_detection)

                with self.frame_lock:
                    self.frame = resized  # 存储调整大小后的BGR帧
                    self.last_update = time.time()
                    self.fps_counter += 1

                if time.time() - self.last_fps_time >= 1.0:
                    self.current_fps = self.fps_counter
                    self.fps_counter = 0
                    self.last_fps_time = time.time()

                elapsed = time.time() - start_time
                sleep_time = max(0.0, (1 / Config_AICV.FPS) - elapsed)
                time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"摄像头 {self.cam_id} 处理异常: {str(e)}")
                self.status = f"错误: {str(e)}"
                self.retry_count += 1
                time.sleep(1)

        if self.retry_count >= self.max_retries:
            self.status = "离线（超过最大重试次数）"
            logger.error(f"摄像头 {self.cam_id} 超过最大重试次数，停止尝试")

    def _send_phone_alert(self, frame):
        """发送手机检测警报"""
        try:
            success, buffer = cv2.imencode('.jpg', frame, [
                int(cv2.IMWRITE_JPEG_QUALITY), 90  # 提高JPEG质量
            ])
            if not success:
                logger.error(f"摄像头 {self.cam_id} 图像编码失败")
                return

            threading.Thread(
                target=self._send_alert_request,
                args=(buffer.tobytes(),),
                daemon=True
            ).start()
        except Exception as e:
            logger.error(f"摄像头 {self.cam_id} 警报处理异常: {str(e)}")

    def _send_alert_request(self, image_bytes):
        """实际发送API请求"""
        try:
            # 获取映射后的摄像头ID
            mapped_id = Config_AICV.CAMERA_ID_MAPPING.get(self.cam_id, f"unknown_{self.cam_id}")

            params = {'cameraId': mapped_id}
            files = {'file': ('alert.jpg', image_bytes, 'image/jpeg')}

            # 添加调试日志
            logger.debug(f"发送警报参数: {params}")

            response = requests.post(
                Config_AICV.ALERT_API,
                params=params,
                files=files,
                timeout=5
            )

            # 处理非200状态码
            if response.status_code != 200:
                logger.error(f"API返回异常状态码: {response.status_code}")
                return

            result = response.json()
            if result.get('result') == 0:
                logger.info(f"警报发送成功: {result.get('message')}")
            else:
                logger.warning(f"服务端返回错误: {result.get('message')}")

        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求异常: {str(e)}")
        except Exception as e:
            logger.error(f"处理响应异常: {str(e)}")

    def reconnect(self):
        try:
            if self.cap:
                self.cap.release()
            time.sleep(1)
            self.cap = self._init_camera()
            self.status = "运行中"
        except Exception as e:
            self.status = f"重连失败: {str(e)}"
            logger.error(f"摄像头 {self.cam_id} 重连失败: {str(e)}")

    def get_jpeg(self):
        with self.frame_lock:
            if (time.time() - self.last_update) > 5:
                return None, self.status, 0

            try:
                success, buffer = cv2.imencode('.jpg', self.frame, [
                    int(cv2.IMWRITE_JPEG_QUALITY), Config_AICV.JPEG_QUALITY
                ])
                return buffer.tobytes() if success else None, self.status, self.current_fps
            except Exception as e:
                logger.error(f"摄像头 {self.cam_id} 帧编码失败: {str(e)}")
                return None, f"编码错误: {str(e)}", 0


# 初始化摄像头系统
camera_system = {}
for cam_id in Config_AICV.CAMERAS:
    try:
        camera_system[cam_id] = CameraProcessor(cam_id, cam_id)
        time.sleep(1)
    except Exception as e:
        logger.error(f"摄像头 {cam_id} 初始化失败: {str(e)}")
        camera_system[cam_id] = None


@app.route('/')  # 主页路径
def dashboard():
    cameras = []
    for cam_id, cam in camera_system.items():
        status = cam.status if cam else '离线'
        cameras.append({
            'id': cam_id,
            'name': Config_AICV.CAMERAS.get(cam_id, f"Camera_{cam_id}"),
            'status': status
        })

    return render_template('dashboard3.html',
                           cameras=cameras,
                           display_size=Config_AICV.DISPLAY_SIZE,
                           fps=Config_AICV.FPS,
                           server_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           device=Config_AICV.DEVICE)


@app.route('/camera_detail/<int:cam_id>')
def camera_detail(cam_id):
    cam = camera_system.get(cam_id)
    cam_name = Config_AICV.CAMERAS.get(cam_id, f"Camera_{cam_id}")
    status = cam.status if cam else "离线"
    return render_template('camera_detail.html',
                           cam_id=cam_id,
                           cam_name=cam_name,
                           status=status)


@app.route('/api/detection_stats/<int:cam_id>')
def detection_stats(cam_id):
    cam = camera_system.get(cam_id)
    if not cam or not cam.last_detection:
        return jsonify({})

    class_counts = {}
    confidences = []
    details = []
    for det in cam.detection_history:
        class_name = det['class']
        class_counts[class_name] = class_counts.get(class_name, 0) + 1
        confidences.append(det['confidence'])
        details.append({
            "timestamp": det['timestamp'] * 1000,
            "class": class_name,
            "confidence": det['confidence']
        })

    sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)

    return jsonify({
        "labels": [c[0] for c in sorted_classes],
        "counts": [c[1] for c in sorted_classes],
        "confidences": confidences[-10:],
        "details": details[-10:]
    })


@app.route('/video/<int:cam_id>')
def video_feed(cam_id):
    def generate():
        last_active = time.time()
        while True:
            try:
                cam = camera_system.get(cam_id)
                if cam is None:
                    time.sleep(1)
                    continue

                frame, status, fps = cam.get_jpeg()
                if frame is None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n\r\n')
                    time.sleep(0.5)
                    continue

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

                elapsed = time.time() - last_active
                sleep_time = max(0.0, (1 / Config_AICV.FPS) - elapsed)
                time.sleep(sleep_time)
                last_active = time.time()

            except Exception as e:
                logger.error(f"视频流 {cam_id} 生成异常: {str(e)}")
                time.sleep(1)

    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/camera_status')
def camera_status():
    status = []
    for cam_id, cam in camera_system.items():
        if cam:
            objects = [d['class'] for d in cam.last_detection]
            status.append({
                'id': cam_id,
                'name': cam.cam_name,
                'status': cam.status,
                'fps': cam.current_fps,
                'last_update': cam.last_update,
                'objects': objects
            })
        else:
            status.append({
                'id': cam_id,
                'name': Config_AICV.CAMERAS.get(cam_id, f"Camera_{cam_id}"),
                'status': '离线',
                'fps': 0,
                'last_update': 0,
                'objects': []
            })
    return jsonify(status)


@app.route('/api/status')
def system_status():
    cameras = []
    for cam_id, cam in camera_system.items():
        if cam:
            objects = [d['class'] for d in cam.last_detection]
            cameras.append({
                'id': cam_id,
                'name': cam.cam_name,
                'status': cam.status,
                'fps': cam.current_fps,
                'objects': objects
            })
        else:
            cameras.append({
                'id': cam_id,
                'name': Config_AICV.CAMERAS.get(cam_id, f"Camera_{cam_id}"),
                'status': '离线',
                'fps': 0,
                'objects': []
            })

    return jsonify({
        'cameras': cameras,
        'system': {
            'cpu': np.random.randint(30, 70),
            'memory': np.random.randint(40, 80)
        }
    })


if __name__ == '__main__':
    try:
        logger.info("启动增强版视频监控系统...")
        logger.info(f"系统配置: FPS={Config_AICV.FPS}, 设备={Config_AICV.DEVICE}, 分辨率={Config_AICV.DISPLAY_SIZE}")
        app.run(host='0.0.0.0', port=5000, threaded=True)
    except KeyboardInterrupt:
        logger.info("接收到中断信号，关闭系统...")