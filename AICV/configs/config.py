import torch
class Config_AICV:
    CAMERAS = {
        0: "Myself",
        # 1: "刘一畅房间摄像头",
        # 2: "熊懿房间摄像头",
        # 3: "冯海芹房间摄像头",
        # 4: "熊懿房间摄像头",
    }
    DISPLAY_SIZE = (640, 320)
    FPS = 15
    MODEL = "yolov10s.pt"
    JPEG_QUALITY = 80
    BUFFER_SIZE = 2
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    # 新增警报配置
    ALERT_API = "http://36.133.69.73:11112/api/monitoringcenter/videowarn"  # 警报接收的API地址
    ALERT_COOLDOWN = 10  # 警报冷却时间（秒）
    TARGET_CONFIDENCE = 0.6  # 目标检测置信度阈值
    CLASS_BOX_NAME = ["cell phone", "bottle", "cup"]  # 所需检测目标的名称
    # 新增摄像头ID映射（根据服务端要求配置）
    CAMERA_ID_MAPPING = {
        0: "j0005",
        # 1: "j0001",  # 本地摄像头1 对应服务端j0001
        # 2: "j0002",
        # 3: "j0003",
        # 4: "j0004",
    }