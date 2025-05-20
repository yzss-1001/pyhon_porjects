import os
import shutil
from sklearn.model_selection import train_test_split

val_size = 0.2
#输入
postfix = 'jpg'
imgpath = r'D:\python\AICV\model\train\data\origin_data'
txtpath =  r'D:\python\AICV\model\train\data\origin_data_mark'

#结果输出
output_train_img_folder = r'D:\python\AICV\model\train\data\train\images'
output_val_img_folder = r'D:\python\AICV\model\train\data\val\images'
output_train_txt_folder = r'D:\python\AICV\model\train\data\train\labels'
output_val_txt_folder = r'D:\python\AICV\model\train\data\val\labels'

os.makedirs(output_train_img_folder, exist_ok=True)
os.makedirs(output_val_img_folder, exist_ok=True)
os.makedirs(output_train_txt_folder, exist_ok=True)
os.makedirs(output_val_txt_folder, exist_ok=True)


listdir = [i for i in os.listdir(txtpath) if 'txt' in i]
train, val = train_test_split(listdir, test_size=val_size, shuffle=True, random_state=0)


for i in train:
    if i[:-4] != "classes":
        img_source_path = os.path.join(imgpath, '{}.{}'.format(i[:-4], postfix))  # classes.txt这个文件可以去掉, 否则没有对应图片.
        txt_source_path = os.path.join(txtpath, i)

        img_destination_path = os.path.join(output_train_img_folder, '{}.{}'.format(i[:-4], postfix))
        txt_destination_path = os.path.join(output_train_txt_folder, i)

        shutil.copy(img_source_path, img_destination_path)
        shutil.copy(txt_source_path, txt_destination_path)

for i in val:
    if i[:-4] != "classes":
        img_source_path = os.path.join(imgpath, '{}.{}'.format(i[:-4], postfix))
        txt_source_path = os.path.join(txtpath, i)

        img_destination_path = os.path.join(output_val_img_folder, '{}.{}'.format(i[:-4], postfix))
        txt_destination_path = os.path.join(output_val_txt_folder, i)

        shutil.copy(img_source_path, img_destination_path)
        shutil.copy(txt_source_path, txt_destination_path)

