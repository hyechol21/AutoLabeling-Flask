import os
import natsort
import shutil
import color

class LoadData():
    def __init__(self, path):
        self.folder_path = path  # 폴더 경로
        self.obj_data = dict()
        self.obj_names = []
        self.img_list = []  # 이미지 파일 경로
        self.img_count = 0
        # self.boxes = {}
        self.boxes = []
        self.colors = []

    # 전체 이미지의 데이터 저장
    def save(self, path, i):
        with open(path, 'w') as f:
            for box in self.boxes[i]:
                cx = box[1] + box[3] / 2
                cy = box[2] + box[4] / 2
                line = "{} {:.6f} {:.6f} {:.6f} {:.6f}\n".format(box[0], round(cx, 6), round(cy, 6),
                                                                 round(box[3], 6), round(box[4], 6))
                f.write(line)

    def save_meta_all(self):
        for i in range(self.img_count):
            txt_path = self.img_list[i][:-3]+'txt' # .jpg 대신 .txt로 파일 쓰기
            self.save(txt_path, i)

    # 현재 작업한 이미지 1장의 데이터 저장
    def save_meta_single(self, i):
        txt_path = self.img_list[i][:-3]+'txt'
        self.save(txt_path, i)

    # 현재 이미지 파일 관련 데이터 삭제
    def delete_image(self, i):
        image_path = self.img_list[i]
        path = os.path.splitext(image_path)[0]

        del self.img_list[i]
        del self.boxes[i]
        self.img_count -= 1
        del_path = os.path.join(self.folder_path, 'delete')

        if not os.path.isdir(del_path):
            os.mkdir(del_path)
        shutil.move(image_path, del_path)

        if os.path.isfile(path + '.txt'):
            shutil.move(path + '.txt', del_path)

        if os.path.isfile(path + '.json'):
            shutil.move(path + '.json', del_path)

    # obj.data 파일 읽기
    def open_obj_data(self):
        try:
            with open(os.path.join(self.folder_path, "obj.data")) as f:
                for line in f:
                    try:
                        key, value = line.split('=')
                        key = key.strip()
                        value = value.strip()

                        if key in ['train', 'names']:
                            value = value.split('/')[-1]
                            self.obj_data[key] = os.path.join(self.folder_path, value)
                    except:
                        pass
        except:
            return False
        return True

    # 레이블 이름 파일 읽기
    def open_obj_names(self):
        global colors
        with open(self.obj_data['names']) as f:
            self.obj_names = [name.strip() for name in f if len(name.strip()) != 0]
            self.colors = color.get_color(len(self.obj_names))
            self.colors = color.get_color_2(len(self.obj_names))

    # train.txt 파일 읽기
    def open_train(self):
        self.create_train()
        self.read_train()
        # print(self.img_list)
        # if os.path.isfile(self.obj_data['train']):
        #     self.read_train()
        #     print(self.img_list)
        # else:
        #     self.create_train()
        #     print(self.img_list)
        #     print("train 파일 생성")

    # train.txt 파일 읽기
    def read_train(self):
        with open(self.obj_data['train'], 'r') as f:
            self.img_list = [path.strip() for path in f if len(path.strip())!=0]

    # train.txt 파일 생성
    def create_train(self):
        img_path = os.path.join(self.folder_path, "img")
        # print(sorted(os.listdir(img_path)))
        file_list = [file for file in os.listdir(img_path) if file.endswith(('jpg', 'bmp', 'png'))]
        file_list = natsort.natsorted(file_list)

        with open(self.obj_data['train'], 'w') as f:
            for file in file_list:
                line = os.path.join(img_path, file)
            #     # 원하는 라벨링 객체가 있는 이미지만 뽑아내기
            #     point = line[:line.rfind('.')]
            #     meta_path = line[:line.rfind('.')] + '.txt'
            #     # meta_path = os.path.join(line.split('.')[:-1], 'txt')
            #     print(meta_path)
            #     with open(meta_path, 'r') as check_f:
            #         lines = check_f.readlines()
            #         # print('pass')
            #         check = False
            #         for x in lines:
            #             label_idx = x.split()[0]
            #             if int(label_idx) == 1:
            #                 check = True
            #         if check:
            #             f.write(line + '\n')
            #             self.img_count += 1
                f.write(line + '\n')
                self.img_count += 1

    # 박스 데이터 불러오기
    def load_box(self):
        for i in range(self.img_count):
            file_txt = self.img_list[i][:-3] + 'txt'

            # self.boxes[i] = []
            self.boxes.append([])
            if os.path.isfile(file_txt):
                with open(file_txt, 'r') as f:
                    for line in f:
                        box = list(map(float, line.split()))
                        box[0] = int(box[0])
                        box[1] = round(box[1] - box[3]/2, 6)
                        box[2] = round(box[2] - box[4]/2, 6)
                        self.boxes[i].append(box)

    # 해당 페이지의 박스 데이터 저장
    # def save_meta(self, idx):
    #     txt_path = self.img_list[idx][:-3]+'txt' # .jpg 대신 .txt로 파일 쓰기
    #
    #     with open(txt_path, 'w') as f:
    #         for box in self.boxes[idx]:
    #             cx = box[1] + box[3] / 2
    #             cy = box[2] + box[4] / 2
    #             line = "{} {:.6f} {:.6f} {:.6f} {:.6f}\n".format(box[0], round(cx, 6), round(cy, 6),
    #                                                              round(box[3], 6), round(box[4], 6))
    #             f.write(line)
