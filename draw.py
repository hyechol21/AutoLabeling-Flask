import sys
import copy
import load_data
import image_label
import shortcuts
import requests
import base64
import json
import theme4
from functools import wraps

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPixmap, QColor, QCursor, QFont
from PyQt5.QtCore import Qt, QSize


'''
    version 3.1.0
'''


class MainForm(QMainWindow):
    def __init__(self):
        super(MainForm, self).__init__()
        self.window_shortcut = shortcuts.Shortcut()
        self.img = None
        self.meta = None
        self.connected = False
        self.current_idx = 0
        self.current_label_idx = 0
        self.pix = None

        self.pressKey = []
        self.sum_ascii = 0
        self.backup = []
        self.copy_box = None
        self.flag_hide = False
        self.group_buttons = []
        self.dark = False

        self.count_boxes_per_class = dict()
        self.limited_region = []
        self.restrict_model = None

        self.min_max_box_size = [0, 0, 16777245, 16777245]
        # self.color_selected_box = QColor(255, 190, 11)
        self.color_selected_box = QColor('#fce94f')

        self.json_filename = ''
        self.json_data = {}

        self.initUI()
        self.open()


    def initUI(self):
        self.setObjectName("MainWindow")
        self.resize(1280, 720)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(480, 360))
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.drawLabel = image_label.MyLabel()
        self.drawLabel.min_max_box_size = self.min_max_box_size
        self.drawLabel.color_selected_box = self.color_selected_box
        # self.drawLabel.setFocusPolicy(Qt.NoFocus)
        sizePolicy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.drawLabel.sizePolicy().hasHeightForWidth())
        self.drawLabel.setSizePolicy(sizePolicy)
        self.drawLabel.setAlignment(Qt.AlignCenter)
        self.drawLabel.setIndent(-1)
        self.drawLabel.setObjectName("drawLabel")
        self.horizontalLayout.addWidget(self.drawLabel)

        # Tab1
        self.verticalLayout_tab1 = QVBoxLayout()
        self.objectList = QListWidget(self.centralwidget)
        self.objectList.setFocusPolicy(Qt.NoFocus)
        self.objectList.setMinimumSize(QSize(100, 0))
        self.objectList.setMaximumSize(QSize(250, 200))
        self.objectList.setObjectName("objectList")
        self.verticalLayout_tab1.addWidget(self.objectList)

        self.hbox = QHBoxLayout()
        self.hbox.setContentsMargins(5, 10, 5, 5)
        self.hbox.setObjectName('hbox')
        self.slider = QSlider(Qt.Horizontal, self.centralwidget)
        self.slider.setFocusPolicy(Qt.NoFocus)
        self.slider.setObjectName("slider")
        self.slider.setMinimumWidth(100)
        self.slider.setMaximumWidth(250)
        self.hbox.addWidget(self.slider)
        self.verticalLayout_tab1.addLayout(self.hbox)

        self.pageLabel = QLabel(self.centralwidget)
        self.pageLabel.setAlignment(Qt.AlignCenter)
        self.pageLabel.setObjectName("pageLabel")
        self.verticalLayout_tab1.addWidget(self.pageLabel)

        self.fileList = QListWidget(self.centralwidget)
        self.fileList.setFocusPolicy(Qt.NoFocus)
        self.fileList.setMinimumSize(QSize(100, 0))
        self.fileList.setMaximumSize(QSize(250, 16777215))
        self.fileList.setObjectName("fileList")
        self.verticalLayout_tab1.addWidget(self.fileList)


        # 사람 옷 색상, 종류
        colors = ['빨강', '주황', '노랑', '초록', '파랑', '갈색', '보라', '라임', '핑크', '회색', '검정', '흰색']
        top = ['알수없음', '민소매', '긴팔', '반팔', '원피스', '롱패딩', '코트']
        bottom = ['알수없음', '긴바지', '짧은바지', '긴치마', '짧은치마']
        sex = ['알수없음', '남성', '여성']
        hair = ['알수없음', '대머리', '단발', '장발']

        json_colors = ['red', 'orange', 'yellow', 'green', 'blue', 'brown', 'purple', 'lime', 'pink', 'gray', 'black', 'white']
        json_upper = ['unknown', 'sleeveless', 'longSleeve','shortSleeve', 'onePiece', 'longPadding', 'coat']
        json_lower = ['unknown', 'longPants', 'shortPants', 'longSkirt', 'shortSkirt']
        json_gender = ['unknown', 'male', 'female']
        json_hair = ['unknown', 'noHair', 'shortHair', 'longHair']


        self.attribute_btn_list = {
            0: ['gender', json_gender],
            1: ['hair', json_hair],
            2: ['upper', json_upper],
            3: ['lower', json_lower],
            4: ['top_color', json_colors],
            5: ['bottom_color', json_colors]
        }

        self.group_list = []

        group_sex = self.group(sex, 3)
        group_hair = self.group(hair, 2)

        group_top = self.group(top, 2)
        group_bottom = self.group(bottom, 2)

        group_top_color = self.group(colors, 2)
        group_bottom_color = self.group(colors, 2)

        # 사람 성벌, 헤어
        group_box_sex = QGroupBox('성별')
        group_box_sex.setMaximumHeight(200)
        group_box_sex.setLayout(group_sex)

        group_box_hair = QGroupBox('헤어')
        group_box_hair.setMaximumHeight(200)
        group_box_hair.setLayout(group_hair)

        # 옷 종류 영역
        group_box_top = QGroupBox('상의')
        group_box_top.setMaximumHeight(300)
        group_box_top.setLayout(group_top)

        group_box_bottom = QGroupBox('하의')
        group_box_bottom.setMaximumHeight(300)
        group_box_bottom.setLayout(group_bottom)

        # 옷 생상 영역
        group_box_top_color = QGroupBox('상의 색상')
        group_box_top_color.setMaximumHeight(300)
        group_box_top_color.setLayout(group_top_color)

        group_box_bottom_color = QGroupBox('하의 색상')
        group_box_bottom_color.setMaximumHeight(300)
        group_box_bottom_color.setLayout(group_bottom_color)

        self.remove_attribute_btn = QPushButton('삭제')
        self.remove_attribute_btn.setCheckable(True)
        self.remove_attribute_btn.setStyleSheet("QPushButton{background-color: #FF0000; color: rgb(50,50,50);}"
                                                "QPushButton::checked{background-color: rgb(200,200,200); }"
                                                )
        self.remove_attribute_btn.clicked.connect(self.remove_attribute)

        self.verticalLayout_tab_person = QVBoxLayout()
        self.verticalLayout_tab_person.addWidget(group_box_sex)
        self.verticalLayout_tab_person.addWidget(group_box_hair)
        # self.verticalLayout_tab_person.addWidget(self.remove_attribute_btn)

        self.verticalLayout_tab_clothes = QVBoxLayout()
        self.verticalLayout_tab_clothes.addWidget(group_box_top)
        self.verticalLayout_tab_clothes.addWidget(group_box_bottom)
        self.verticalLayout_tab_clothes.addWidget(self.remove_attribute_btn)

        self.verticalLayout_tab_color = QVBoxLayout()
        self.verticalLayout_tab_color.addWidget(group_box_top_color)
        self.verticalLayout_tab_color.addWidget(group_box_bottom_color)

        # 속성 탭
        # 박스 속성 설정
        self.box_size_edit = []
        for i in range(4):
            self.box_size_edit.append(QLineEdit())
            text = str(self.min_max_box_size[i])
            self.box_size_edit[i].setText(text)

        self.box_size_edit[0].editingFinished.connect(lambda: self.set_box_size_satndard(0))
        self.box_size_edit[1].editingFinished.connect(lambda: self.set_box_size_satndard(1))
        self.box_size_edit[2].editingFinished.connect(lambda: self.set_box_size_satndard(2))
        self.box_size_edit[3].editingFinished.connect(lambda: self.set_box_size_satndard(3))

        self.min_box_size_layout = QHBoxLayout()
        self.min_box_size_layout.addWidget(self.box_size_edit[0])
        self.min_box_size_layout.addWidget(QLabel("x"))
        self.min_box_size_layout.addWidget(self.box_size_edit[1])

        self.max_box_size_layout = QHBoxLayout()
        self.max_box_size_layout.addWidget(self.box_size_edit[2])
        self.max_box_size_layout.addWidget(QLabel("x"))
        self.max_box_size_layout.addWidget(self.box_size_edit[3])

        self.color_selected_box_btn = QPushButton()
        self.color_selected_box_btn.setStyleSheet('background-color: %s' % self.color_selected_box.name())
        self.color_selected_box_btn.clicked.connect(self.show_color_dialog)

        self.formLayout_box = QFormLayout()
        self.formLayout_box.addRow("최소 크기: ", self.min_box_size_layout)
        self.formLayout_box.addRow("최대 크기: ", self.max_box_size_layout)
        self.formLayout_box.addRow("선택 박스 색상: ", self.color_selected_box_btn)

        # 그리기 제한 영역 설정
        self.draw_restrict_btn = QPushButton('영역 생성')
        self.remove_restrict_btn = QPushButton('삭제')
        self.complete_restrict_btn = QPushButton('추가')
        self.restrict_list = QListWidget()

        self.draw_restrict_btn.setStyleSheet('background-color: rgb(210, 210, 210); color:rgb(30, 30, 30)')
        self.remove_restrict_btn.setStyleSheet('background-color: rgb(210, 210, 210); color:rgb(30, 30, 30)')
        self.complete_restrict_btn.setStyleSheet('background-color: rgb(210, 210, 210); color:rgb(30, 30, 30)')

        self.draw_restrict_btn.setFocusPolicy(Qt.NoFocus)
        self.remove_restrict_btn.setFocusPolicy(Qt.NoFocus)
        self.complete_restrict_btn.setFocusPolicy(Qt.NoFocus)
        self.restrict_list.setFocusPolicy(Qt.NoFocus)
        self.remove_attribute_btn.setFocusPolicy(Qt.NoFocus)

        self.draw_restrict_btn.clicked.connect(self.draw_restrict_area)
        self.remove_restrict_btn.clicked.connect(self.remove_restrict_area)
        self.complete_restrict_btn.clicked.connect(self.complete_restrict_area)
        self.restrict_list.itemClicked.connect(self.get_item_restrict)

        self.restrict_layout = QHBoxLayout()
        self.restrict_layout.addWidget(self.remove_restrict_btn)
        self.restrict_layout.addWidget(self.complete_restrict_btn)

        self.formLayout_restrict = QFormLayout()
        self.formLayout_restrict.addRow(self.draw_restrict_btn)
        self.formLayout_restrict.addRow(self.restrict_layout)
        self.formLayout_restrict.addRow(self.restrict_list)

        setting_box = QGroupBox('박스 속성')
        setting_box.setMaximumHeight(200)
        setting_box.setLayout(self.formLayout_box)

        setting_restrict_area = QGroupBox("그리기 제한 영역 설정")
        setting_restrict_area.setMaximumHeight(300)
        setting_restrict_area.setLayout(self.formLayout_restrict)

        self.verticalLayout_tab2 = QVBoxLayout()
        self.verticalLayout_tab2.addWidget(setting_box)
        self.verticalLayout_tab2.addWidget(setting_restrict_area)

        self.tabs = QTabWidget()
        self.tabs.setMaximumSize(QSize(250, 16777215))
        self.tabs.setFocusPolicy(Qt.NoFocus)

        self.tab1 = QWidget()
        self.tab1.layout = self.verticalLayout_tab1
        self.tab1.setLayout(self.tab1.layout)

        self.tab2 = QWidget()
        self.tab2.layout = self.verticalLayout_tab2
        self.tab2.setLayout(self.tab2.layout)

        self.tab_color = QWidget()
        self.tab_color.layout = self.verticalLayout_tab_color
        self.tab_color.setLayout(self.tab_color.layout)

        self.tab_clothes = QWidget()
        self.tab_clothes.layout = self.verticalLayout_tab_clothes
        self.tab_clothes.setLayout(self.tab_clothes.layout)

        self.tab_person = QWidget()
        self.tab_person.layout = self.verticalLayout_tab_person
        self.tab_person.setLayout(self.tab_person.layout)

        # 탭 추가
        self.tabs.addTab(self.tab1, "기본")
        self.tabs.addTab(self.tab2, "속성")
        self.tabs.addTab(self.tab_person, "사람")
        self.tabs.addTab(self.tab_clothes, "옷 종류")
        self.tabs.addTab(self.tab_color, "옷 색상")

        self.horizontalLayout.addWidget(self.tabs)

        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.tabs, 0, 2)

        self.setCentralWidget(self.centralwidget)

        # 툴바
        openAction = QAction(QIcon('./icon/icons8-add-folder-30.png'), '폴더 열기', self)
        openAction.triggered.connect(self.open)

        saveAction = QAction(QIcon('./icon/icons8-save-48 (1).png'), '저장', self)
        saveAction.triggered.connect(self.save)

        settingAction = QAction(QIcon('./icon/icons8-keyboard-30 (3).png'), '단축키 설정', self)
        settingAction.triggered.connect(self.settings)

        self.leftAction = QAction(QIcon('./icon/icons8-arrow-pointing-left-24.png'), '이전 이미지', self)
        self.leftAction.triggered.connect(self.left)

        self.rightAction = QAction(QIcon('./icon/icons8-arrow-24.png'), '다음 이미지', self)
        self.rightAction.triggered.connect(self.right)

        self.labelLeftAction = QAction(QIcon('./icon/icons8-back-to-30.png'), '이전 레이블', self)
        self.labelLeftAction.triggered.connect(self.lebel_left)

        self.labelRightAction = QAction(QIcon('./icon/icons8-next-page-30.png'), '다음 레이블', self)
        self.labelRightAction.triggered.connect(self.label_right)

        self.action_hide = QAction(QIcon('./icon/icons8-eye-40.png'), '텍스트 보기', self)
        self.action_hide.triggered.connect(self.hide)
        self.action_hide.setCheckable(True)

        self.indicateAction = QAction(QIcon('./icon/icons8-target-32 (1).png'), '크로스라인 보기')
        self.indicateAction.triggered.connect(self.indicate)
        self.indicateAction.setCheckable(True)

        self.drawAction = QAction(QIcon('./icon/icons8-box-30.png'), '박스 그리기', self)
        self.drawAction.triggered.connect(self.draw)
        self.drawAction.setCheckable(True)

        self.thicknessCombo = QComboBox()
        self.thicknessCombo.setFocusPolicy(Qt.NoFocus)
        self.thicknessCombo.addItems(['선 굵기', '1', '2', '3', '4', '5', '6'])
        self.thicknessCombo.activated[str].connect(self.thickness)
        self.thicknessCombo.model().item(0).setEnabled(False)

        self.action_select = QAction(QIcon('./icon/icons8-selection-128.png'), '박스 선택', self)
        # self.action_select = QAction(QIcon('./icon/icons8-selection-60.png'), '박스 선택', self)
        self.action_select.triggered.connect(self.select)
        self.action_select.setCheckable(True)

        copyAction = QAction(QIcon('./icon/icons8-copy-48 (1).png'), '박스 복사', self)
        copyAction.triggered.connect(self.copy)

        pasteAction = QAction(QIcon('./icon/icons8-paste-30.png'), '박스 붙여넣기', self)
        pasteAction.triggered.connect(self.paste)

        undoAction = QAction(QIcon('./icon/icons8-delete-48.png'), '박스 삭제', self)
        undoAction.triggered.connect(self.undo)

        removeAction = QAction(QIcon('./icon/icons8-remove-24.png'), '현재 이미지 모든 박스 삭제', self)
        removeAction.triggered.connect(self.remove)

        restoreAction = QAction(QIcon('./icon/icons8-undo-24.png'), '되돌리기', self)
        restoreAction.triggered.connect(self.restore)

        self.zoomInAction = QAction(QIcon('./icon/icons8-zoom-in-24.png'), '화면 확대', self)
        self.zoomInAction.triggered.connect(self.zoom_in)
        self.zoomInAction.setCheckable(True)

        self.zoomOutAction = QAction(QIcon('./icon/icons8-zoom-out-24.png'), '화면 축소', self)
        self.zoomOutAction.triggered.connect(self.zoom_out)
        self.zoomOutAction.setCheckable(True)

        self.moveFocusAction = QAction(QIcon('./icon/icons8-drag-24.png'), '포커싱 이동', self)
        self.moveFocusAction.triggered.connect(self.move_focus)
        self.moveFocusAction.setCheckable(True)

        self.autoCombo = QComboBox(self)
        self.autoCombo.setFocusPolicy(Qt.NoFocus)
        self.autoCombo.addItem('Auto Label')

        self.autoAction = QAction(QIcon('./icon/icons8-ok-48.png'), '오토 라벨링 실행', self)
        self.autoAction.triggered.connect(self.request_prediction)

        self.darkModeAction = QAction(QIcon('./icon/sun.png'), '다크모드', self)
        self.darkModeAction.triggered.connect(self.on_dark)

        self.spacer = QWidget()
        self.spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.toolbar = QToolBar('tool')
        self.addToolBar(self.toolbar)
        self.toolbar.addAction(openAction)
        self.toolbar.addAction(saveAction)
        self.toolbar.addAction(settingAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_hide)
        self.toolbar.addAction(self.indicateAction)
        self.toolbar.addAction(self.leftAction)
        self.toolbar.addAction(self.rightAction)
        self.toolbar.addAction(self.labelLeftAction)
        self.toolbar.addAction(self.labelRightAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_hide)
        self.toolbar.addAction(self.indicateAction)
        self.toolbar.addAction(self.drawAction)
        self.toolbar.addWidget(self.thicknessCombo)
        self.toolbar.addAction(self.action_select)
        self.toolbar.addAction(copyAction)
        self.toolbar.addAction(pasteAction)
        self.toolbar.addAction(undoAction)
        self.toolbar.addAction(removeAction)
        self.toolbar.addAction(restoreAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.zoomInAction)
        self.toolbar.addAction(self.zoomOutAction)
        self.toolbar.addAction(self.moveFocusAction)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.autoCombo)
        self.toolbar.addAction(self.autoAction)
        # self.toolbar.addAction(self.restrictAction)
        self.toolbar.addWidget(self.spacer)
        self.toolbar.addAction(self.darkModeAction)

        # 이미지 뷰어
        self.drawLabel.RectSignal.connect(self.draw_box)
        self.drawLabel.setMouseTracking(True)
        # 레이블 목록
        self.objectList.itemClicked.connect(self.object_itemSelection)
        # 파일 리스트
        self.fileList.itemClicked.connect(self.image_itemSelection)
        # 이미지 슬라이더
        self.slider.valueChanged.connect(self.slide)
        self.slider.sliderPressed.connect(self.slide_start)
        # 다크 모드로 세팅
        self.on_dark()
        self.drawLabel.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.drawLabel)
        self.center()
        self.setWindowTitle("4IND")
        self.show()

    # 탭의 라디오 그룹 생성
    def group(self, contents, space=2):
        grid = QGridLayout()

        self.group_list.append(QButtonGroup())
        self.group_list[-1].setExclusive(False)

        group_idx = len(self.group_list) - 1
        self.group_list[-1].buttonClicked[int].connect(lambda: self.on_clicked(group_idx))

        btns = []
        for i in range(len(contents)):
            btn = QPushButton(contents[i])
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setCheckable(True)

            btn.setFont(QFont('Bold', 11))
            btn.setStyleSheet("QPushButton{background-color: rgb(210, 210, 210); color: rgb(30, 30, 30)}"
                              "QPushButton::checked{background-color: rgb(52, 140, 228);}")
            self.group_list[-1].addButton(btn, i)
            row = i // space
            col = i % space
            grid.addWidget(btn, row, col)
            btns.append(btn)
        self.group_buttons.append(btns)
        return grid

    # 버튼 선택 / 해제
    def on_clicked(self, group_idx):
        if self.connected:
            id = self.group_list[group_idx].checkedId()
            attribute_group = self.attribute_btn_list[group_idx][0]
            attribute_group_btn = self.attribute_btn_list[group_idx][1][id]

            for i in range(len(self.group_buttons[group_idx])):
                self.group_buttons[group_idx][i].setChecked(False)

            if id != -1:
                self.group_buttons[group_idx][id].setChecked(True)
                temp = self.json_data.copy()
                temp[attribute_group] = attribute_group_btn

                self.json_data = {}
                for key, val in self.attribute_btn_list.items():
                    if val[0] in temp.keys():
                        self.json_data[val[0]] = temp[val[0]]
                if 'etc' in temp.keys():
                    self.json_data['etc'] = 'remove'
            else:
                del self.json_data[attribute_group]
            set_json_file(self.json_filename, self.json_data, True)

    def remove_attribute(self):
        if self.connected:
            if self.remove_attribute_btn.isChecked():
                self.json_data['etc'] = 'remove'
            else:
                del self.json_data['etc']

            set_json_file(self.json_filename, self.json_data, True)

    # 박스 크기 설정 값이 올바른 숫자인지 검사하는 데코레이터
    def check_edit(function):
        @wraps(function)
        def wrapper(self, *args, **kwargs):
            edit_idx = args[0]
            edit = self.box_size_edit[edit_idx]
            text = edit.text().strip()
            # print(text)
            if not text.isdecimal():
                text = str(self.min_max_box_size[edit_idx])
            self.box_size_edit[edit_idx].setText(text)
            function(self, *args, **kwargs)
        return wrapper

    @check_edit
    def set_box_size_satndard(self, idx):
        self.drawLabel.min_max_box_size[idx] = int(self.box_size_edit[idx].text())

    def show_color_dialog(self):
        color = QColorDialog.getColor()
        # print(color.name())
        if color.isValid():
            self.color_selected_box_btn.setStyleSheet("background-color: %s" % color.name())
            self.drawLabel.color_selected_box = color.name()
            self.drawLabel.zoom_update()

    def on_dark(self):
        if self.dark:
            # print('라이트 모드 ON')
            self.dark = False
            theme4.light(app)
            for group in self.group_buttons:
                for btn in group:
                    btn.setStyleSheet("QPushButton{background-color: rgb(210, 210, 210); color: rgb(30, 30, 30)}"
                                      "QPushButton::checked{background-color: rgb(52, 140, 228);}")
                    self.darkModeAction.setIcon(QIcon("./icon/sun.png"))
                    self.darkModeAction.setText('다크모드 변경')
        else:
            # print('다크 모드 ON')
            self.dark = True
            theme4.dark(app)
            for group in self.group_buttons:
                for btn in group:
                    btn.setStyleSheet("QPushButton{background-color: rgb(60, 60, 60); color: rgb(180, 180, 180)}"
                                      "QPushButton::checked{background-color: #003366;}")
                    self.darkModeAction.setIcon(QIcon('./icon/moon4.png'))
                    self.darkModeAction.setText('라이트모드 변경')

    def settings(self):
        self.window_shortcut = shortcuts.Shortcut()
        self.window_shortcut.exec_()

    def keyPressEvent(self, event):
        shortcut = self.window_shortcut.key_ascii
        # print(event.key())
        if self.drawLabel.flag_carry or self.drawLabel.flag_resize:
            pass
        else:
            if event.key()==32:
                if not event.isAutoRepeat():
                    self.pressKey.append(event.key())
            else:
                self.pressKey.append(event.key())
            self.sum_ascii = sum(self.pressKey)

            if not self.drawLabel.priority:
                # 레이블 번호 키패드 번호와 일치 (0번은 물결)
                if 47 < self.sum_ascii < 48 + self.objectList.count():
                    try:
                        self.get_item_label(int(event.text()))
                    except:
                        pass

                if self.sum_ascii == 96:
                    self.get_item_label(int(0))

                # 스페이스바 누르고 박스 그리기
                if self.sum_ascii == 32 and not event.isAutoRepeat():
                    self.drawLabel.priority = True
                    self.drawLabel.deactivate_select()
                    self.drawLabel.setCursor(QCursor(Qt.CrossCursor))
                    if self.indicateAction.isChecked():
                        self.drawLabel.indicator = True
                    # 박스 감추기
                    self.drawLabel.boxes = []
                    self.drawLabel.deactivate_select()
                    self.drawLabel.zoom_update()
                elif self.sum_ascii == Qt.Key_Escape:
                    self.exit()
                elif self.sum_ascii == shortcut['KEY_OPEN']:
                    self.open()
                    self.pressKey = []
                    self.sum_ascii = 0
                elif self.sum_ascii == shortcut['KEY_SAVE']:
                    self.save()
                    self.pressKey = []
                    self.sum_ascii = 0
                elif self.sum_ascii == shortcut['KEY_SETTING']:
                    self.settings()
                    self.pressKey = []
                    self.sum_ascii = 0
                elif self.sum_ascii == shortcut['KEY_TEXT']:
                    self.action_hide.toggle()
                    self.hide()
                elif self.sum_ascii == shortcut['KEY_CROSSLINE']:
                    self.indicateAction.toggle()
                    self.indicate()
                elif self.sum_ascii == shortcut['KEY_IMAGE_BEFORE']:
                    self.left()
                elif self.sum_ascii == shortcut['KEY_IMAGE_AFTER']:
                    self.right()
                elif self.sum_ascii == shortcut['KEY_LABEL_BEFORE']:
                    self.lebel_left()
                elif self.sum_ascii == shortcut['KEY_LABEL_AFTER']:
                    self.label_right()
                elif self.sum_ascii == shortcut['KEY_DRAW']:
                    self.drawAction.toggle()
                    self.draw()
                elif self.sum_ascii == shortcut['KEY_SELECT']:
                    self.action_select.toggle()
                    self.select()
                elif self.sum_ascii == shortcut['KEY_COPY']:
                    self.copy()
                elif self.sum_ascii == shortcut['KEY_PASTE']:
                    self.paste()
                elif self.sum_ascii == shortcut['KEY_QUICK']:
                    self.quick()
                elif self.sum_ascii == shortcut['KEY_UNDO']:
                    self.undo()
                elif self.sum_ascii == shortcut['KEY_REMOVE']:
                    self.remove()
                elif self.sum_ascii == shortcut['KEY_RESTORE']:
                    self.restore()
                elif self.sum_ascii == shortcut['KEY_ALTERNATE_MOUSE']:
                    self.alternate_mouse()
                elif self.sum_ascii == shortcut['KEY_DELETE_FILE']:
                    self.delete_file()
                else:
                    if len(self.pressKey) == 2:
                        self.pressKey = []
                        self.sum_ascii = 0

    def keyReleaseEvent(self, event):
        # print('Release: ', event.key())
        if event.key() in self.pressKey:
            if event.key()==32:
                if not event.isAutoRepeat():
                    self.drawLabel.priority = False
                    self.pressKey.remove(event.key())
                    self.drawLabel.setCursor(self.change_cursor())
                    if not self.drawAction.isChecked():
                        self.drawLabel.indicator = False
                    self.drawLabel.boxes = self.meta.boxes[self.current_idx]
                    self.drawLabel.flag = False
                    self.drawLabel.zoom_update()
            else:
                self.pressKey.remove(event.key())

    def change_cursor(self):
        if self.drawAction.isChecked():
            cursor = QCursor(Qt.CrossCursor)
        elif self.zoomInAction.isChecked():
            cursor = QCursor(QPixmap("./icon/icons8-zoom-in-24.png"), -1, -1)
        elif self.zoomOutAction.isChecked():
            cursor = QCursor(QPixmap("./icon/icons8-zoom-out-24.png"), -1, -1)
        elif self.moveFocusAction.isChecked():
            cursor = QCursor(Qt.ClosedHandCursor)
        elif self.drawLabel.action_restrict_area:
            cursor = QCursor(Qt.CrossCursor)
        else:
            cursor = QCursor(Qt.ArrowCursor)
        return cursor

    # 클래스별 박스 개수
    def classes_box_count(self):
        for i in range(len(self.meta.obj_names)):
            self.count_boxes_per_class[i] = 0

        for box in self.meta.boxes[self.current_idx]:
            self.count_boxes_per_class[box[0]] += 1

        for i in range(len(self.meta.obj_names)):
            text = f'{i}  {self.meta.obj_names[i]}\t\t{str(self.count_boxes_per_class[i])}'
            self.objectList.item(i).setText(text)

    def class_box_count(self, idx, sign):
        self.count_boxes_per_class[idx] += (sign)
        text = f'{idx}  {self.meta.obj_names[idx]}\t\t{str(self.count_boxes_per_class[idx])}'
        self.objectList.item(idx).setText(text)

    # 시그널이 올때 슬롯 : 박스 그리기
    def draw_box(self, x, y, w, h):
        x, y = round(x, 6), round(y, 6)
        w, h = round(w, 6), round(h, 6)

        self.meta.boxes[self.current_idx].append([self.current_label_idx, x, y, w, h])
        if self.drawLabel.priority:
            self.drawLabel.boxes = [[self.current_label_idx, x, y, w, h]]
        else:
            self.drawLabel.boxes = self.meta.boxes[self.current_idx]
        self.class_box_count(self.current_label_idx, 1)

    # flask 서버에 현재 이미지에 대한 예측 수행결과 request
    def request_prediction(self):
        if self.connected:
            name = str(self.autoCombo.currentText())
            index = self.autoCombo.currentIndex() - 1

            url = "http://localhost:5050/prediction"

            img_64_encode = base64.b64encode(self.img)
            img_str = img_64_encode.decode('utf-8')

            params = {"label": name, "img": img_str}

            try:
                res = requests.post(url, data=json.dumps(params))
                if not res:
                    return

                for box in res.json()['box']:
                    box.insert(0, index)
                    box[1], box[2] = self.drawLabel.check_load_box(box[1], box[2], box[3], box[4])
                    self.meta.boxes[self.current_idx].append(box)
                self.drawLabel.boxes = self.meta.boxes[self.current_idx]
                self.drawLabel.zoom_update()
            except:
                pass

    # 이미지 처음 보일 때
    def show_image(self):
        self.drawLabel.select_index = None
        self.drawLabel.select_box = []
        self.deactivate_strict_area()

        img = open(self.meta.img_list[self.current_idx], 'rb')
        self.img = img.read()

        self.pix = self.drawLabel.set_image(self.meta.img_list[self.current_idx], self.meta.boxes[self.current_idx], self.limited_region[self.current_idx])

        self.pageLabel.setText(str(self.current_idx + 1) + ' / ' + str(self.meta.img_count))
        self.drawLabel.connected = True
        self.classes_box_count()

        filename = self.meta.img_list[self.current_idx]
        self.json_filename = filename.replace(filename.split('.')[-1], 'json')
        try:
            self.json_data = get_json_file(self.json_filename)
        except:
            self.json_data = {}
        # print(self.json_data)
        for group in self.group_buttons:
            for btn in group:
                btn.setChecked(False)
        cur = 0
        for key, val in self.json_data.items():
            for i in range(cur, len(self.attribute_btn_list)):
                attr = self.attribute_btn_list[i]
                if key == attr[0]:
                    idx = attr[1].index(val)
                    self.group_buttons[i][idx].setChecked(True)
                    cur = i+1
        if 'etc' in self.json_data.keys() and self.json_data['etc'] == 'remove':
                self.remove_attribute_btn.setChecked(True)
        else:
            self.remove_attribute_btn.setChecked(False)

    # moouse click 대신 키보드 단축키로 바운딩박스 좌표 찍기
    def alternate_mouse(self):
        if self.connected:
            self.drawLabel.set_box_point()

    # 슬라이더가 눌렸을 때, 현재 작업중이던 이미지의 데이터 저장
    def slide_start(self):
        if self.connected:
            self.meta.save_meta_single(self.current_idx)

    def slide(self):
        if self.connected:
            if self.slider.value() != self.current_idx:
                self.get_item_image_slider(self.slider.value())

    # Label Name의 현재 항목 얻어오기
    def object_itemSelection(self):
        self.current_label_idx = self.objectList.currentRow()
        self.drawLabel.color_idx = self.current_label_idx
        text = self.objectList.currentItem().text()
        text, _ = text.split('\t\t')
        self.drawLabel.label_name = text
        if self.action_hide.isChecked():
            self.drawLabel.zoom_update()

    def image_itemSelection(self):
        cur_idx = self.fileList.currentRow()
        if cur_idx != self.current_idx:
            self.meta.save_meta_single(self.current_idx)
            self.current_idx = self.fileList.currentRow()
            self.slider.setValue(self.current_idx)
            self.show_image()
            self.load_restrict_area()

    def save(self):
        if self.connected:
            self.meta.save_meta_all()
            self.success_alert('저장되었습니다.')

    def exit(self):
        if self.connected:
            self.meta.save_meta_all()
        sys.exit()

    # 이전 이미지
    def left(self):
        if self.connected:
            self.get_item_image(self.current_idx - 1)

    # 다음 이미지
    def right(self):
        if self.connected:
            self.get_item_image(self.current_idx + 1)

    # 이전 레이블
    def lebel_left(self):
        if self.connected:
            if self.drawLabel.select_index is None:
                self.get_item_label(self.current_label_idx - 1)
            else:
                idx = self.drawLabel.select_box[0] - 1
                self.change_selected_box_label(idx)

    # 다음 레이블
    def label_right(self):
        if self.connected:
            if self.drawLabel.select_index is None:
                self.get_item_label(self.current_label_idx + 1)
            else:
                idx = self.drawLabel.select_box[0] + 1
                self.change_selected_box_label(idx)

    # 화면 텍스트 감추기
    def hide(self):
        if self.connected:
            action = self.action_hide.isChecked()
            if action:
                self.drawLabel.action_hide = True
            else:
                self.drawLabel.action_hide = False
            self.drawLabel.zoom_update()
        else:
            self.action_hide.setChecked(False)

    def indicate(self):
        if self.connected:
            action = self.indicateAction.isChecked()
            if action and self.drawAction.isChecked():
                self.drawLabel.indicator = True
            else:
                self.drawLabel.indicator = False
                self.drawLabel.flag = False
                self.drawLabel.update()

    def thickness(self, text):
        if self.connected:
            self.drawLabel.thickness = int(text)
            self.drawLabel.zoom_update()

    # 박스 그리기
    def draw(self):
        if self.connected:
            action = self.drawAction.isChecked()
            self.deactivate()
            if action:
                self.drawAction.setChecked(True)
                self.drawLabel.action_paint = True
                self.drawLabel.setCursor(QCursor(Qt.CrossCursor))

                if self.indicateAction.isChecked():
                    self.drawLabel.indicator = True
                self.wait()
            elif self.action_select.isChecked():
                self.drawLabel.action_select = True
        else:
            self.drawAction.setChecked(False)

    # 박스 선택하기
    def select(self):
        if self.connected:
            action = self.action_select.isChecked()

            if action:
                self.drawLabel.action_select = True
            else:
                self.drawLabel.action_select = False
        else:
            self.action_select.setChecked(False)

    # 현재 이미지의 모든 박스 복사 - 다음 이미지로 넘기기 - 박스 붙여넣기
    def quick(self):
        if self.connected:
            if self.drawLabel.select_box:
                self.drawLabel.deactivate_select()
            self.copy()
            self.right()
            self.paste()

    # 현재 이미지의 박스 전체 복사
    def copy(self):
        if self.connected:
            if self.drawLabel.select_box:
                self.copy_box = [self.meta.boxes[self.current_idx][self.drawLabel.select_index]]
            else:
                self.copy_box = self.meta.boxes[self.current_idx]

    # 현재 이미지에 복사된 박스 붙여넣기
    def paste(self):
        if self.connected and self.copy_box:
            if self.drawLabel.select_box:
                self.drawLabel.deactivate_select()
            for box in copy.deepcopy(self.copy_box):
                if box in self.meta.boxes[self.current_idx]:
                    pass
                else:
                    self.meta.boxes[self.current_idx].append(box)
            # self.meta.boxes[self.current_idx] += copy.deepcopy(self.copy_box)
            self.drawLabel.zoom_update()
            self.classes_box_count()

    # 이전 박스 데이터 삭제
    def undo(self):
        if self.connected:
            if len(self.meta.boxes[self.current_idx]) > 0:
                # 선택된 박스가 있다면 해당박스 삭제
                if self.drawLabel.select_box:
                    temp = [self.meta.boxes[self.current_idx].pop(self.drawLabel.select_index)]
                    self.drawLabel.select_box = []
                    self.drawLabel.select_index = None
                    self.drawLabel.setCursor(self.change_cursor())
                # 마우스 커서가 가르키는 박스 삭제
                elif self.drawLabel.active_box:
                    temp = [self.meta.boxes[self.current_idx].pop(self.drawLabel.active_index)]
                    self.drawLabel.active_box = []
                    self.drawLabel.active_index = None
                # 마지막 생성 박스부터 차례로 삭제
                else:
                    temp = [self.meta.boxes[self.current_idx].pop()]
                # print(temp[0][0])
                self.class_box_count(temp[0][0], -1)
                self.backup[self.current_idx].append(temp)
                self.drawLabel.boxes = self.meta.boxes[self.current_idx]
                self.drawLabel.zoom_update()

    # 현재 이미지의 박스 전체 삭제
    def remove(self):
        if self.connected:
            if len(self.meta.boxes[self.current_idx]) > 0:
                self.backup[self.current_idx].append(self.meta.boxes[self.current_idx].copy())
                self.meta.boxes[self.current_idx] = []
                self.drawLabel.deactivate_select()
                self.drawLabel.boxes = []
                self.drawLabel.zoom_update()
                self.drawLabel.setCursor(self.change_cursor())
                self.classes_box_count()

    # 현재 이미지 파일 삭제 (delete 폴더에 옮기기)
    def delete_file(self):
        if self.connected:
            if self.drawLabel.select_box:
                self.drawLabel.deactivate_select()
            print('이미지 파일 삭제!')
            self.meta.delete_image(self.current_idx)

            if self.meta.img_count == 0:
                self.reset()
                return

            if self.current_idx < len(self.limited_region):
                del self.limited_region[self.current_idx]

            if self.current_idx < len(self.backup):
                del self.backup[self.current_idx]

            self.fileList.takeItem(self.current_idx)

            if self.current_idx == self.meta.img_count:
                self.current_idx = 0
            self.fileList.setCurrentRow(self.current_idx)
            self.show_image()
            self.slider.setValue(self.current_idx)
            # self.load_restrict_area()
            # self.get_item_image(self.current_idx)

    # 되돌리기
    def restore(self):
        if self.connected:
            if self.backup[self.current_idx]:
                for box in self.backup[self.current_idx].pop():
                    self.meta.boxes[self.current_idx].append(box)
                    self.drawLabel.boxes = self.meta.boxes[self.current_idx]
                self.drawLabel.zoom_update()
                self.classes_box_count()

    # 화면 배율 확대
    def zoom_in(self):
        if self.connected:
            action = self.zoomInAction.isChecked()
            self.deactivate()
            if action:
                self.zoomInAction.setChecked(True)
                self.drawLabel.action_zoom_plus = True
                cursor_zoom_in = QCursor(QPixmap("./icon/icons8-zoom-in-24.png"), -1, -1)
                self.drawLabel.setCursor(cursor_zoom_in)
                self.wait()
            elif self.action_select.isChecked():
                self.drawLabel.action_select = True
        else:
            self.zoomInAction.setChecked(False)

    # 화면 배율 축소
    def zoom_out(self):
        if self.connected:
            action = self.zoomOutAction.isChecked()
            self.deactivate()
            if action:
                self.zoomOutAction.setChecked(True)
                self.drawLabel.action_zoom_minus = True
                cursor_zoom_out = QCursor(QPixmap("./icon/icons8-zoom-out-24.png"), -1, -1)
                self.drawLabel.setCursor(cursor_zoom_out)
                self.wait()
            elif self.action_select.isChecked():
                self.drawLabel.action_select = True
        else:
            self.zoomOutAction.setChecked(False)

    # 이미지 포커싱 이동
    def move_focus(self):
        if self.connected:
            action = self.moveFocusAction.isChecked()
            self.deactivate()
            if action:
                self.moveFocusAction.setChecked(True)
                self.drawLabel.action_focus = True
                self.drawLabel.setCursor(QCursor(Qt.ClosedHandCursor))
                self.wait()
            elif self.action_select.isChecked():
                self.drawLabel.action_select = True
        else:
            self.moveFocusAction.setChecked(False)

    def get_item_restrict(self):
        idx = self.restrict_list.currentRow()
        if idx == self.drawLabel.selected_poly:
            self.deactivate_strict_area()
        else:
            self.drawLabel.selected_poly = idx
        self.drawLabel.zoom_update()

    # 현재 이미지의 제한 영역 목록 불러오기
    def load_restrict_area(self):
        self.restrict_list.clear()
        for i in range(len(self.limited_region[self.current_idx])):
            item = f'금지 영역 {i}'
            self.restrict_list.addItem(item)

    # 제한 영역 그리기
    def draw_restrict_area(self):
        if self.connected:
            self.deactivate()
            self.deactivate_strict_area()
            self.drawLabel.deactivate_select()
            self.drawLabel.action_restrict_area = True
            self.drawLabel.setCursor(QCursor(Qt.CrossCursor))

    # 현재 이미지에 선택된 제한 영역 삭제
    def remove_restrict_area(self):
        if self.connected:
            if self.drawLabel.action_restrict_area:
                self.drawLabel.action_restrict_area = False
                self.drawLabel.setCursor(QCursor(Qt.ArrowCursor))
                self.drawLabel.poly = []
                self.drawLabel.update()
            else:
                idx = self.restrict_list.selectedIndexes()
                if not idx: # 선택 안했는 경우
                    pass
                else:
                    idx = self.restrict_list.currentRow()
                    self.restrict_list.takeItem(idx)
                    del self.limited_region[self.current_idx][idx]
                    self.drawLabel.zoom_update()

                    for i in range(idx, self.restrict_list.count()):
                        item = f'금지 영역 {i}'
                        self.restrict_list.item(i).setText(item)

    # 현재 이미지에 제한 영역 추가
    def complete_restrict_area(self):
        if self.connected:
            self.drawLabel.action_restrict_area = False
            self.drawLabel.setCursor(QCursor(Qt.ArrowCursor))
            if self.drawLabel.poly:
                self.limited_region[self.current_idx].append(copy.deepcopy(self.drawLabel.poly))
                idx = len(self.limited_region[self.current_idx])-1
                item = f'금지 영역 {idx}'
                self.restrict_list.addItem(item)
                self.drawLabel.poly = []
                self.drawLabel.zoom_update()

    def wait(self):
        # 그리기 툴바 선택시 박스 선택 옵션 사라지게
        self.drawLabel.action_select = False
        if self.drawAction.isChecked():
            self.drawLabel.deactivate_select()
        else:
            self.drawLabel.disappear = False

    def deactivate_strict_area(self):
        self.restrict_list.clearSelection()
        self.drawLabel.selected_poly = None
        # print(self.restrict_list.selectedIndexes())

    def deactivate(self):
        self.drawAction.setChecked(False)
        self.moveFocusAction.setChecked(False)
        self.zoomInAction.setChecked(False)
        self.zoomOutAction.setChecked(False)
        self.drawLabel.action_paint = False
        self.drawLabel.action_focus = False
        self.drawLabel.action_zoom_plus = False
        self.drawLabel.action_zoom_minus = False

        if self.drawLabel.action_restrict_area:
            self.drawLabel.setCursor(QCursor(Qt.CrossCursor))
        else:
            self.drawLabel.setCursor((QCursor(Qt.ArrowCursor)))
        self.drawLabel.indicator = False
        self.drawLabel.flag = False
        self.drawLabel.update()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # 폴더 불러올때 기존의 데이터 초기화
    def reset(self):
        if self.meta is not None:
            self.meta.save_meta_all()

        self.meta = None
        self.connected = False
        self.current_idx = 0
        self.current_label_idx = 0
        self.pix = None
        self.backup = []
        self.copy_box = None
        self.json_filename = ''
        self.json_data = {}

        self.objectList.clear()
        self.fileList.clear()
        self.autoCombo.clear()
        self.autoCombo.addItem('Auto Label')
        self.restrict_list.clear()
        self.deactivate()
        self.action_hide.setChecked(False)
        self.drawLabel.action_hide = False
        self.action_select.setChecked(False)
        self.drawLabel.action_select = False
        self.thicknessCombo.setEnabled(False)
        self.remove_attribute_btn.setChecked(False)

        for group in self.group_buttons:
            for btn in group:
                btn.setChecked(False)
        self.drawLabel.connected = False
        self.drawLabel.zoom_reset()
        self.drawLabel.setPixmap(QPixmap())

    def open(self):
        path = QFileDialog.getExistingDirectory(self, '폴더 선택')  # 폴더 경로 반환
        # 폴더 선택 안했을 경우
        if path == "":
            print('선택 안함')
            self.thicknessCombo.setEnabled(False)
            return
        # 폴더 다시 여는 경우 데이터 초기화
        print(path)
        print(path.rfind('data'))
        self.reset()
        self.meta = load_data.LoadData(path)

        ret = self.meta.open_obj_data()

        if not ret:
            self.error_alert("잘못된 폴더입니다.")
            return

        self.meta.open_obj_names()
        self.meta.open_train()

        if len(self.meta.obj_names) == 0:
            self.error_alert('레이블이 존재하지 않습니다.')
            return
        if len(self.meta.img_list) == 0:
            self.error_alert('이미지가 존재하지 않습니다.')
            return

        # 각 이미지의 박스 데이터 불러오기
        self.meta.load_box()
        self.drawLabel.label_list = self.meta.obj_names
        self.drawLabel.colors = self.meta.colors

        # 레이블 이름 불러오기
        for i in range(len(self.meta.obj_names)):
            item = QListWidgetItem(self.meta.obj_names[i])
            item.setForeground(QColor(self.meta.colors[i]))
            self.objectList.addItem(item)

        # 이미지 파일 이름 불러오기
        for i in range(len(self.meta.img_list)):
            self.fileList.insertItem(i, self.meta.img_list[i].split('/')[-1])
            self.backup.append([])
            self.limited_region.append([])

        self.slider.setRange(0, self.meta.img_count-1)
        self.connected = True
        self.get_item_label(0)
        self.get_item_image_slider(0)

        self.action_hide.toggle()
        self.hide()
        self.indicateAction.toggle()

        self.action_select.toggle()
        self.select()
        self.thicknessCombo.setEnabled(True)
        # self.autoCombo.addItems(self.meta.obj_names)

    def change_selected_box_label(self, idx):
        length = len(self.meta.obj_names)
        idx = (length + idx) % length
        self.meta.boxes[self.current_idx][self.drawLabel.select_index][0] = idx
        self.classes_box_count()
        if self.action_hide.isChecked():
            self.drawLabel.zoom_update()

    def get_item_label(self, idx):
        length = len(self.meta.obj_names)
        idx = (length + idx) % length
        self.current_label_idx = idx
        self.objectList.setCurrentRow(self.current_label_idx)
        self.drawLabel.color_idx = self.current_label_idx
        self.drawLabel.label_name = self.objectList.currentItem().text().split('\t\t')[0]
        if self.action_hide.isChecked():
            self.drawLabel.zoom_update()

    # 이미지 불러오기
    def get_item_image(self, idx):
        self.meta.save_meta_single(self.current_idx) # 작업중이던 이미지 저장
        self.current_idx = (self.meta.img_count + idx) % self.meta.img_count
        self.fileList.setCurrentRow(self.current_idx)
        self.show_image()
        self.slider.setValue(self.current_idx)
        self.load_restrict_area()

    def get_item_image_slider(self, idx):
        # if self.
        self.current_idx = (self.meta.img_count + idx) % self.meta.img_count
        self.fileList.setCurrentRow(self.current_idx)
        self.show_image()
        self.slider.setValue(self.current_idx)
        self.load_restrict_area()

    def success_alert(self, msg):
        alert = QMessageBox()
        alert.setWindowTitle("성공")
        alert.setText(msg)
        alert.setIcon(QMessageBox.Information)
        alert.exec_()

    def error_alert(self, msg):
        alert = QMessageBox()
        alert.setWindowTitle("오류")
        alert.setText(msg)
        alert.setIcon(QMessageBox.Critical)
        alert.exec_()

    def closeEvent(self, QCloseEvent):
        ans = QMessageBox.question(self, "종료", "종료 하시겠습니까?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)  # 마지막 값은 기본값
        if ans == QMessageBox.Yes:  # Yes 클릭시 종료
            if self.connected:
                self.meta.save_meta_all()
            QCloseEvent.accept()
        else:
            QCloseEvent.ignore()

def get_json_file(filepath, is_print=False):
    with open(filepath, 'r') as f:
        json_data = json.load(f)
        if is_print:
            print(json.dupmps(json_data, indent='\t'))
    return json_data

def set_json_file(filepath, json_data, is_print=False):
    if is_print:
        print(json.dumps(json_data, indent='\t'))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent='\t')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    widget = MainForm()
    sys.exit(app.exec_())

