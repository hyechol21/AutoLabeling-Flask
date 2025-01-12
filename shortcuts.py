from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import set_control

class Shortcut(QDialog):
    def __init__(self):
        super().__init__()

        self.setting = set_control.setControl()
        self.cur_shortcut = {}
        self.overlap = False

        self.row = None
        self.col = None
        self.r_click = False

        self.key_control = {'Ctrl': Qt.Key_Control, 'Shift': Qt.Key_Shift, 'Alt': Qt.Key_Alt}
        self.key_etc = {
            'F1': Qt.Key_F1, 'F2': Qt.Key_F2, 'F3': Qt.Key_F3, 'F4': Qt.Key_F4,
            'F5': Qt.Key_F5, 'F6': Qt.Key_F6, 'F7': Qt.Key_F7, 'F8': Qt.Key_F8,
            'F9': Qt.Key_F9, 'F10': Qt.Key_F10, 'F11': Qt.Key_F11, 'F12': Qt.Key_F12,
            'Escape': Qt.Key_Escape, 'Tab': Qt.Key_Tab, 'CapsLock': Qt.Key_CapsLock,
            'Backspace': Qt.Key_Backspace, 'Enter': Qt.Key_Return,
            'Insert': Qt.Key_Insert, 'Delete': Qt.Key_Delete, 'Home': Qt.Key_Home,
            'End': Qt.Key_End, 'PageUp': Qt.Key_PageUp, 'PageDown': Qt.Key_PageDown,
            'Left': Qt.Key_Left, 'Right': Qt.Key_Right, 'Up': Qt.Key_Up, 'Down': Qt.Key_Down
        }
        self.key_ascii = {}
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle('단축키 설정')
        self.setMinimumSize(450, 600)

        self.key1 = QComboBox()
        self.key2 = QComboBox()

        self.table = QTableWidget()
        self.table.setFocusPolicy(Qt.NoFocus)
        self.set_table()

        self.alert = QLabel()
        self.alert.setAlignment(Qt.AlignCenter)
        self.alert.setStyleSheet("Color: red")

        btn_reset = QPushButton('초기화')
        btn_reset.clicked.connect(self.reset)

        btn_ok = QPushButton('확인')
        btn_ok.clicked.connect(self.apply)

        btn_cancle = QPushButton('취소')
        btn_cancle.clicked.connect(self.cancle)

        layout = QGridLayout()
        layout.addWidget(self.table, 0, 0, 5, 5)
        layout.addWidget(self.alert, 5, 1, 1, 3)
        layout.addWidget(btn_reset, 6, 1)
        layout.addWidget(btn_ok, 6, 2)
        layout.addWidget(btn_cancle, 6, 3)

        # self.table.cellClicked.connect( self.set_key)
        self.table.cellPressed.connect(self.set_key)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.viewport().installEventFilter(self)
        self.setLayout(layout)

    def set_key(self):
        self.row = self.table.currentRow()
        self.col = self.table.currentColumn()
        self.empty()

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.RightButton:
                self.r_click = True
            elif event.button() == Qt.LeftButton:
                self.r_click = False
            return False
        else:
            return False

    def empty(self):
        if self.r_click:
            self.table.takeItem(self.row, self.col)

    def set_ascii_key(self, shortcut):
        for key, value in shortcut.items():
            res = 0
            for x in value:
                if x in self.key_control.keys():
                    res += self.key_control[x]
                elif x in self.key_etc.keys():
                    res += self.key_etc[x]
                else:
                    res += ord(x)
            self.key_ascii[key] = res

    # default_shortcut 읽어오기
    # 임시 변수에 저장해놓고 table에 띄어주기
    # 확인 버튼 누르면
    def reset(self):
        self.cur_shortcut = dict()
        for key, val in self.setting.default_shortcut.items():
            val = val.strip('[]')
            m = val.split(']')

            self.cur_shortcut[key] = []
            for x in m:
                x = x.strip('[]')
                self.cur_shortcut[key].append(x)
        self.set_table_data(self.cur_shortcut)

    def apply(self):
        # 중복키가 있으면 레이블로 경고하고 저장안되게 하기
        # for key, value in self.cur_shortcut.items():
        if not self.overlap:
            self.setting.update_ini(self.cur_shortcut)
            self.set_ascii_key(self.cur_shortcut)
            self.close()

    def cancle(self):
        self.close()

    def check_overlap(self):
        temp = list(self.cur_shortcut.values())
        for i in range(len(temp)):
            if temp[i] in temp[i + 1:]:
                self.overlap = True
                self.alert.setText('중복키가 존재합니다.')
                break
        else:
            self.overlap = False
            self.alert.setText('')

    def set_table_data(self, dict_shortcut):
        i = 0
        for key, val in dict_shortcut.items():
            if len(val) > 1:
                self.table.setItem(i+1, 1, QTableWidgetItem(val[0]))
                self.table.setItem(i+1, 2, QTableWidgetItem(val[1]))
            elif len(val) == 1:
                self.table.setItem(i+1, 2, QTableWidgetItem(val[0]))
            i += 1

    def set_table(self):
        self.cur_shortcut = self.setting.custom_shortcut
        self.set_ascii_key(self.cur_shortcut)

        headers = ['기능', '키1', '키2']
        contents = ['폴더 열기', '저장', '단축키 설정', '텍스트 보이기', '크로스라인 보이기', '이전 이미지', '다음 이미지',
                    '이전 레이블', '다음 레이블', '박스 그리기', '박스 선택', '박스 복사', '박스 붙여넣기', '퀵 박스 복사',
                    '선택 박스 삭제', '전체 박스 삭제', '되돌리기', '박스 점 클릭 대체키 설정', '이미지 파일 삭제']

        header = self.table.horizontalHeader()

        self.table.setColumnCount(3)
        self.table.setRowCount(len(contents)+1)

        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        self.table.setCellWidget(0, 1, self.key1)
        self.table.setCellWidget(0, 2, self.key2)

        for i in range(len(contents)):
            self.table.setItem(i+1, 0, QTableWidgetItem(contents[i]))

        self.set_table_data(self.setting.custom_shortcut)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)


    def keyReleaseEvent(self, e):
        new_key = None

        if self.row and self.col:
            dict_key = list(self.cur_shortcut)[self.row-1]
            dict_idx = 0

            if self.col == 1:
                for key, value in self.key_control.items():
                    if e.key() == value:
                        new_key = key
            elif self.col == 2:
                if e.key() < 94:
                    if 47 < e.key() < 59 or e.key==96:
                        pass
                    else:
                        new_key = chr(e.key())
                        if len(self.cur_shortcut[dict_key]) > 1:
                            dict_idx = 1
                else:
                    for key, value in self.key_etc.items():
                        if e.key() == value:
                            new_key = key
                            if len(self.cur_shortcut[dict_key]) > 1:
                                dict_idx = 1

        if new_key:
            self.table.setItem(self.row, self.col, QTableWidgetItem(new_key))
            self.cur_shortcut[dict_key][dict_idx] = new_key
            self.check_overlap()














