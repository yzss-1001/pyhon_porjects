from ultralytics import YOLO
if __name__ == '__main__':
    # Load a model
    model = YOLO(model=r'D:\python\AICV\weights\yolov10s.pt')  # 这里是原模型，也可用自己训练过后的模型。
    model.predict(source=r'D:\python\AICV\model\run\detect_photo',  # 调用摄像头则为0, 这里是模型用来推理的资源.
                  save=True,
                  show=True,
                  device='cpu',  # 指定运行推理的设备,我的电脑无显卡，所以用cpu
                  augment=True,  # 使用数据增强
                  project=r'D:\python\AICV\model\run\detect_result'  # 保存结果的目录位置
                  )