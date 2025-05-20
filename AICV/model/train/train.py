import warnings
from ultralytics import YOLO
warnings.filterwarnings('ignore')

if __name__ == '__main__':
    model = YOLO(model=r'D:\python\AICV\weights\yolov10s.pt')
    # model.load('yolo11n.pt')  # 加载预训练权重,改进或者做对比实验时候不建议打开，因为用预训练模型整体精度没有很明显的提升
    model.train(data=r'data.yaml',
                device='cpu',  # 指定cpu运行,我的电脑没有GPU,有的话就是device=0 (单个GPU) 或者 device=0,1,2... (多个GPU)
                imgsz=640,
                epochs=300,
                batch=4,
                workers=0,
                optimizer='SGD',  # 使用SGD优化器
                close_mosaic=10,
                resume=False,
                project=r'train_result',  # 训练结果存放的路径
                name='exp',  # 结果文件夹的名字
                single_cls=False,
                cache=False,
                )
