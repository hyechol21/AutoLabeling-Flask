import copy

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImageReader, QCursor, QFont, QPolygon, QBrush, QRegion
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal, QPoint, QPointF


import color
COLORS = color.get_color(100)

# colors = ['#ff0000', '#00ff00', '#0000ff', '#FFFF00', '#74DFF0', '#01DFD7', '#013ADF', '#7401DF', '#151515', '#585858']

class MyLabel(QLabel):
    RectSignal = pyqtSignal(float, float, float, float)  # 박스 좌표 데이터 전송

    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)

        self.connected = False # 사진이 있을 때
        self.action_paint = False
        self.action_select = False
        self.action_focus = False
        self.action_zoom_plus = False
        self.action_zoom_minus = False
        self.action_hide = False
        self.priority = False
        self.indicator = False
        self.thickness = 2
        self.action_restrict_area = False

        self.colors = None
        self.boxes = None
        self.name = None
        self.pix = QPixmap()
        self.img = None
        self.qimage_scaled = None

        self.label_name = None # 현재 선택된 레이블 이름
        self.label_list = []
        self.color_idx = 0
        self.flag = False
        self.flag_zoom = False
        self.st_x = 0
        self.st_y = 0
        self.end_x = 0
        self.end_y = 0
        self.x, self.y, self.w, self.h = 0, 0, 0, 0

        self.zoom_y = 1
        self.position = [0, 0]

        self.move_x = 0
        self.move_y = 0
        self.dx, self.dy = 0,0
        self.anchor = [0,0]
        self.center = None

        self.active_box = []
        self.active_index = None
        self.pos_x = None
        self.pos_y = None

        self.select_index = None
        self.select_box = None
        self.flag_carry = False
        self.past_x, self.past_y = 0,0
        self.diff = [0,0]
        self.disappear = False

        self.quadrant = False
        self.flag_resize = False
        self.swap = None
        self.rx, self.ry = 0, 0

        # 설정
        self.min_max_box_size = None # [min_width, min_height, max_width, max_height]
        self.color_selected_box = None

        self.poly = []
        self.selected_poly = None

    # 이미지 불러오기
    def set_image(self, name, boxes, limit):
        self.name = name
        self.boxes = boxes
        self.limited_region = limit
        self.scale_image()
        return self.pix

    # 좋은 화질로 이미지 출력
    def scale_image(self):
        img = QImageReader(self.name)
        img.setScaledSize(QSize(self.size()))

        self.img = img.read()
        self.qimage_scaled = self.img.scaled(self.width() * self.zoom_y,
                                             self.height() * self.zoom_y, Qt.KeepAspectRatio)
        self.pix = QPixmap.fromImage(self.img)
        self.setPixmap(self.pix)
        self.zoom_update()

    # 화면 크기 이벤트
    def resizeEvent(self, event):
        try:
            self.scale_image()
            self.show_boxes()
        except:
            pass

    def wheelEvent(self, event):
        if self.connected:
            if float(self.zoom_y) == 1:
                self.get_center(self.pos_x, self.pos_y)
            if event.angleDelta().y() > 0:
                self.zoom_plus()
            else:
                self.zoom_minus()

    def zoom_plus(self):
        self.zoom_y += 0.25
        px, py = self.position
        px += self.width() / 8
        py += self.height() / 8

        self.position = (px, py)
        self.qimage_scaled = self.img.scaled(self.width() * self.zoom_y,
                                             self.height() * self.zoom_y, Qt.KeepAspectRatio)
        self.zoom_update()

    def zoom_minus(self):
        if self.zoom_y > 1.25:
            self.zoom_y -= 0.25
            px, py = self.position
            px -= self.width() / 8
            py -= self.height() / 8

            self.position = (px, py)
            self.qimage_scaled = self.img.scaled(self.width() * self.zoom_y,
                                                 self.height() * self.zoom_y, Qt.KeepAspectRatio)
            self.zoom_update()
        else:
            self.zoom_reset()

    def zoom_reset(self):
        self.zoom_y = 1
        self.position = [0, 0]
        self.center = None
        self.dx, self.dy = 0, 0
        self.qimage_scaled = self.img.scaled(self.width() * self.zoom_y,
                                                 self.height() * self.zoom_y, Qt.KeepAspectRatio)
        self.zoom_update()

    def zoom_update(self):
        if not self.qimage_scaled.isNull():
            px, py = self.position

            if self.center is not None:
                px = self.center[0] * self.qimage_scaled.width() - self.img.width()/2
                py = self.center[1] * self.qimage_scaled.height() - self.img.height()/2
            # 예외처리
            px, py = self.check_zoom(px, py)

            self.position = (px, py)

            painter = QPainter()
            painter.begin(self.pix)
            painter.drawImage(QPoint(0, 0), self.qimage_scaled,
                              QRect(self.position[0], self.position[1], self.img.width(), self.img.height()))
            painter.end()

            self.setPixmap(self.pix)
            self.show_boxes()
            self.show_polygon()

            if self.flag:
                self.st_x = round(self.qimage_scaled.width() * self.rx - self.position[0])
                self.st_y = round(self.qimage_scaled.height() * self.ry - self.position[1])

    # 화면 포커싱 이동시 스케일된 이미지를 벗어나지 않게 체크
    def check_zoom(self, px, py):
        px = px if (px <= self.qimage_scaled.width() - self.img.width()) else (
                self.qimage_scaled.width() - self.img.width())
        py = py if (py <= self.qimage_scaled.height() - self.img.height()) else (
                self.qimage_scaled.height() - self.img.height())
        px = int(px) if (px >= 0) else 0
        py = int(py) if (py >= 0) else 0
        return (px, py)

    # zoom 했을 때의 박스 그리기
    def show_boxes(self):
        painter = QPainter(self.pix)
        idx = -1
        for box in self.boxes:
            idx += 1
            x = round(self.qimage_scaled.width() * box[1] - self.position[0])
            y = round(self.qimage_scaled.height() * box[2] - self.position[1])
            w = round(self.qimage_scaled.width() * box[3])
            h = round(self.qimage_scaled.height() * box[4])

            if idx == self.select_index:
                self.select_box = [box[0], x, y, w, h]

                if self.disappear:
                    continue

                painter.setPen(QPen(QColor(self.color_selected_box), self.thickness+5))
                painter.drawPoint(x, y)
                painter.drawPoint(x, y + h // 2)
                painter.drawPoint(x, y + h)

                painter.drawPoint(x + w // 2, y)
                painter.drawPoint(x + w // 2, y + h)

                painter.drawPoint(x + w, y)
                painter.drawPoint(x + w, y + h // 2)
                painter.drawPoint(x + w, y + h)

                painter.setPen(QPen(QColor(self.color_selected_box), self.thickness, Qt.SolidLine))
            else:
                painter.setPen(QPen(QColor(self.colors[box[0]]), self.thickness, Qt.SolidLine))

            painter.drawRect(x, y, w, h)

            if self.action_hide:
                painter.setFont(QFont("Verdana", 11))
                text = self.label_list[box[0]].split('\t\t')
                painter.drawText(x, y-5, text[0])

        if self.action_hide:
            self.draw_text(painter)

        painter.end()

        self.setPixmap(self.pix)
        self.active_box = []
        self.active_index = None

        if not self.priority:
            self.focus_box()
            self.update()

    # 좌표를 polygon으로 매핑
    def map_point_to_polygon(self, points):
        temp = []
        for p in points:
            x = round(self.qimage_scaled.width() * p[0] - self.position[0])
            y = round(self.qimage_scaled.height() * p[1] - self.position[1])
            temp.append(QPoint(int(x), int(y)))
        poly = QPolygon(temp)
        return poly

    # 제한 구역 표시
    def show_polygon(self):
        if self.limited_region:
            painter = QPainter(self.pix)
            painter.setBrush(QBrush(Qt.black))
            i = 0
            for area in self.limited_region:
                poly = self.map_point_to_polygon(area)
                if i == self.selected_poly:
                    painter.setBrush(QBrush(Qt.darkGray))
                    painter.setOpacity(0.7)
                    painter.setPen(QPen(QColor('#555753'), 2, Qt.DashDotLine))
                else:
                    painter.setBrush(QBrush(Qt.black))
                    painter.setOpacity(1)
                    painter.setPen(QPen())
                painter.drawPolygon(poly)
                i += 1

            painter.end()
            self.setPixmap(self.pix)

    # 마우스 클릭한 위치에 박스가 있는지 체크
    def focus_check(self, name, x, y, w, h, i):
        if (x < self.pos_x < x + w) and (y < self.pos_y < y + h):
            select = None
            if self.select_index is not None:
                select = self.select_box

            iou = 0
            if i != self.select_index and select and select[1] < self.pos_x < select[1] + select[3] and select[2] < self.pos_y < select[2] + select[4]:
                x1 = max(x, select[1])
                y1 = max(y, select[2])
                x2 = min(x + w, select[1] + select[3])
                y2 = min(y + h, select[2] + select[4])
                iou = (x2 - x1) * (y2 - y1)

            if iou > 0 and iou != (w * h):

                self.active_box = [select[0], select[1], select[2], select[3], select[4]]
                self.active_index = self.select_index
                self.update()

            elif self.active_box and w > self.active_box[3] and h > self.active_box[4]:
                pass
            else:
                self.active_box = [name, x, y, w, h]
                self.active_index = i

                self.update()

    # 박스 선택
    def focus_box(self):
        if not self.pos_x:
            return

        if self.flag_carry:
            name = self.boxes[self.select_index][0]
            x = round(self.qimage_scaled.width() * self.boxes[self.select_index][1] - self.position[0])
            y = round(self.qimage_scaled.height() * self.boxes[self.select_index][2] - self.position[1])
            w = round(self.qimage_scaled.width() * self.boxes[self.select_index][3])
            h = round(self.qimage_scaled.height() * self.boxes[self.select_index][4])
            self.focus_check(name, x, y, w, h, self.select_index)
        else:
            i = 0
            for box in self.boxes:
                x = round(self.qimage_scaled.width() * box[1] - self.position[0])
                y = round(self.qimage_scaled.height() * box[2] - self.position[1])
                w = round(self.qimage_scaled.width() * box[3])
                h = round(self.qimage_scaled.height() * box[4])
                self.focus_check(box[0], x, y, w, h, i)
                i += 1

        if self.active_box:
            if self.pos_x < self.active_box[1] or self.pos_x > self.active_box[1] + self.active_box[3] or \
                    self.pos_y < self.active_box[2] or self.pos_y > self.active_box[2] + self.active_box[4]:
                self.active_box = []
                self.active_index = None
                self.update()

    # 이미지에 글자 그리기 (레이블 / 배율)
    def draw_text(self, qp):
        text_label = "{}: {}".format(self.color_idx, self.label_name)
        text_ratido = "{}%".format(int(self.zoom_y*100))

        qp.setFont(QFont("Verdana", 20))
        qp.setPen(QPen(QColor(self.colors[self.color_idx]), Qt.SolidLine))
        qp.drawText(30, 40, text_label)

        qp.setFont(QFont("Verdana", 15))
        qp.setPen(QPen(Qt.yellow, Qt.SolidLine))
        qp.drawText(self.width()-70, 30, text_ratido)

    # 화면의 center 상대 위치
    def get_center(self, a1, a2):
        self.center = [0, 0]
        self.center[0] = (self.position[0] + a1) / self.qimage_scaled.width()
        self.center[1] = (self.position[1] + a2) / self.qimage_scaled.height()

    # 현재 선택된 박스 해제
    def deactivate_select(self):
        self.select_index = None
        self.select_box = None
        self.flag_carry = False
        self.flag_resize = False
        self.quadrant = None
        self.zoom_update()

    def check_load_box(self, x, y, w, h):
        rad_x = self.position[0] / self.qimage_scaled.width()
        rad_y = self.position[1] / self.qimage_scaled.height()

        x = x if (x + rad_x <= 1 - w) else (1 - w - rad_x)
        y = y if (y + rad_y <= 1 - h) else (1 - h - rad_y)
        x = x if (x + rad_x >= 0) else (0 - rad_x)
        y = y if (y + rad_y >= 0) else (0 - rad_y)
        return (x, y)

    def check_move_box(self, px, py, w, h):
        px = px if (px+self.position[0] <= self.qimage_scaled.width() - w) else (
            self.qimage_scaled.width() - w - self.position[0])
        py = py if (py+self.position[1] <= self.qimage_scaled.height() - h) else (
                self.qimage_scaled.height() - h - self.position[1])
        px = int(px) if (px+self.position[0] >= 0) else 0-self.position[0]
        py = int(py) if (py+self.position[1] >= 0) else 0-self.position[1]
        return (px, py)

    def modify_box(self):
        spare = self.thickness + 5
        xmin = self.select_box[1]
        ymin = self.select_box[2]
        xmax = self.select_box[1] + self.select_box[3]
        ymax = self.select_box[2] + self.select_box[4]

        if self.pos_x < xmin or self.pos_x > xmax or self.pos_y < ymin or self.pos_y > ymax:
            self.setCursor(QCursor(Qt.ArrowCursor))
            return [0, 0, 0, 0]

        map_vertex = [1, 1, 1, 1] # 수정하는 xmin, ymin, xmax, ymax는 1로 세팅
        # 현재 마우스 커서가 어느 모서리를 가르키냐에 따라 선택
        if xmin-spare < self.pos_x < xmin+spare:
            if ymin-spare < self.pos_y < ymin+spare:
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
                map_vertex = [0, 0, 1, 1]
            elif ymax - spare < self.pos_y < ymax+spare:
                self.setCursor(QCursor(Qt.SizeBDiagCursor))
                map_vertex = [0, 1, 1, 0]
            elif ymin+spare < self.pos_y < ymax-spare:
                self.setCursor(QCursor(Qt.SizeHorCursor))
                map_vertex = [0, 0, 1, 0]
        elif xmax-spare < self.pos_x < xmax+spare: # 오른쪽
            if ymin-spare < self.pos_y < ymin+spare: # 위
                self.setCursor(QCursor(Qt.SizeBDiagCursor))
                map_vertex = [1, 0, 0, 1]
            elif ymax-spare < self.pos_y < ymax+spare: # 아래
                self.setCursor(QCursor(Qt.SizeFDiagCursor))
                map_vertex = [1, 1, 0, 0]
            elif ymin+spare < self.pos_y < ymax-spare: # 중앙
                self.setCursor(QCursor(Qt.SizeHorCursor))
                map_vertex = [1, 0, 0, 0]
        elif xmin+spare < self.pos_x < xmax-spare:
            if ymin-spare < self.pos_y < ymin+spare:
                self.setCursor(QCursor(Qt.SizeVerCursor))
                map_vertex = [0, 0, 0, 1]
            elif ymax-spare < self.pos_y < ymax+spare:
                self.setCursor(QCursor(Qt.SizeVerCursor))
                map_vertex = [0, 1, 0, 0]
            else:
                self.setCursor(QCursor(Qt.SizeAllCursor))
        return map_vertex

    def check_resize_box(self, xmin, ymin, xmax, ymax):
        xmin = int(xmin) if (xmin+self.position[0] >= 0) else 0-self.position[0]
        ymin = int(ymin) if (ymin + self.position[1] >= 0) else 0 - self.position[1]
        xmax = xmax if (xmax+self.position[0] <= self.qimage_scaled.width()) else (
                self.qimage_scaled.width() - self.position[0])
        ymax = ymax if (ymax + self.position[1] <= self.qimage_scaled.height()) else (
                self.qimage_scaled.height() - self.position[1])
        return (xmin, ymin, xmax, ymax)

    # 박스 사이즈 변경 조건문
    def check_swap_x(self, pos_x, x):
        if pos_x <= x:
            xmin, xmax = pos_x, x
        else:
            xmin, xmax = x, pos_x
        return xmin, xmax

    def check_swap_y(self, pos_y, y):
        if pos_y <= y:
            ymin, ymax = pos_y, y
        else:
            ymin, ymax = y, pos_y

        return ymin, ymax

    def resize_box(self):
        # 박스 사이즈 변경 전 좌표
        # [0, 0, 1, 0]
        xmin, ymin = self.swap[1], self.swap[2]
        xmax, ymax = xmin + self.swap[3], ymin + self.swap[4]

        x = xmin * self.quadrant[0] + xmax * self.quadrant[2]
        y = ymin * self.quadrant[1] + ymax * self.quadrant[3]

        if sum(self.quadrant)==1 and (self.quadrant[1]==1 or self.quadrant[3]==1): # 수직선의 중앙점
            ymin, ymax = self.check_swap_y(self.pos_y, y)
        elif sum(self.quadrant)==1 and (self.quadrant[0]==1 or self.quadrant[2]==1): # 수평선의 중앙점
            xmin, xmax = self.check_swap_x(self.pos_x, x)
        else:
            ymin, ymax = self.check_swap_y(self.pos_y, y)
            xmin, xmax = self.check_swap_x(self.pos_x, x)

        xmin, ymin, xmax, ymax = self.check_resize_box(xmin, ymin, xmax, ymax)
        self.select_box[1:] = [xmin, ymin, xmax - xmin, ymax - ymin]

    def set_box_point(self):
        if self.action_paint or self.priority:
            self.setCursor(QCursor(Qt.CrossCursor))

            if self.flag:
                self.flag = False
                if self.st_x == self.pos_x and self.st_y == self.pos_y:
                    pass
                elif self.end_x - self.x < self.min_max_box_size[0] and self.end_y - self.y < self.min_max_box_size[1]:
                    print('박스 생성 취소: 설정한 최소 박스 사이즈를 넘지 않습니다.')
                elif self.end_x - self.x > self.min_max_box_size[2] and self.end_y - self.y > self.min_max_box_size[3]:
                    print('박스 생성 취소: 설정한 최대 박스 사이즈를 넘습니다.')
                else:
                    # 스케일된 이미지에서의 좌표 매핑
                    x0 = (self.x + self.position[0]) / self.qimage_scaled.width()
                    y0 = (self.y + self.position[1]) / self.qimage_scaled.height()
                    x1 = (self.end_x + self.position[0]) / self.qimage_scaled.width()
                    y1 = (self.end_y + self.position[1]) / self.qimage_scaled.height()

                    # 좌표가 Polygon에 겹치면 pass
                    rect = QPolygon(QRect(self.x, self.y, self.end_x-self.x, self.end_y-self.y), closed=True)

                    for area in self.limited_region:
                        forbid = self.map_point_to_polygon(area)
                        if rect.intersected(forbid):
                            print('교차!!')
                            self.update()
                            return

                    self.RectSignal.emit(x0, y0, x1 - x0, y1 - y0)
                    self.show_boxes()
            else:
                if self.priority:
                    self.boxes = []
                    self.zoom_update()
                self.flag = True
                self.st_x, self.st_y = self.pos_x, self.pos_y
                self.end_x, self.end_y = self.pos_x, self.pos_y
                self.rx = (self.st_x + self.position[0]) / self.qimage_scaled.width()
                self.ry = (self.st_y + self.position[1]) / self.qimage_scaled.height()

    def mousePressEvent(self, event):
        if self.connected:
                # 화면 이동시 시작 좌표
            if event.button() == Qt.RightButton or self.action_focus:
                self.setCursor(QCursor(Qt.ClosedHandCursor))
                self.flag_zoom = True
                self.center = None

                self.move_x = event.x()
                self.move_y = event.y()
                self.anchor = self.position

            elif self.action_paint or self.priority:
                self.set_box_point()

            elif self.action_zoom_plus:
                self.get_center(event.x(), event.y())
                self.zoom_plus()

            elif self.action_zoom_minus:
                self.get_center(event.x(), event.y())
                self.zoom_minus()

            elif self.action_restrict_area:
                if event.button() == Qt.LeftButton:
                    x = (self.pos_x + self.position[0]) / self.qimage_scaled.width()
                    y = (self.pos_y + self.position[1]) / self.qimage_scaled.height()
                    self.poly.append((x, y))
                    self.update()

            if not self.priority and not self.action_restrict_area:
                # 선택 박스 표시하기
                if event.button() == Qt.LeftButton and self.action_select:
                    # 박스 클릭
                    if self.active_index is not None:
                        self.select_index = self.active_index
                        self.select_box = copy.deepcopy(self.active_box)

                        self.past_x, self.past_y = event.x(), event.y()
                        self.zoom_update()
                        self.update()
                    else:
                        self.flag_carry = False

                    # 박스 resize 시작
                    if self.select_index is not None:
                        self.quadrant = self.modify_box()

                        if sum(self.quadrant)==4:
                            self.flag_carry = True
                        elif 0 < sum(self.quadrant) < 4:
                            self.flag_resize = True
                            self.swap = copy.deepcopy(self.select_box)
                        elif sum(self.quadrant) == 0:
                            self.deactivate_select()

    # Mouse release event
    def mouseReleaseEvent(self, event):
        if self.connected:
            # 화면 이동시 종료 좌표
            if event.button() == Qt.RightButton or self.action_focus:
                if self.action_paint or self.priority:
                    self.setCursor(QCursor(Qt.CrossCursor))
                elif self.action_focus:
                    self.setCursor(QCursor(Qt.ClosedHandCursor))
                elif self.action_restrict_area:
                    self.setCursor(QCursor(Qt.CrossCursor))
                else:
                    self.setCursor(QCursor(Qt.ArrowCursor))

                self.flag_zoom = False

                self.get_center(self.img.width() / 2, self.img.height() / 2)

            if self.flag_carry:
                self.flag_carry = False

                self.boxes[self.select_index][1] = round((self.select_box[1] + self.position[0]) / self.qimage_scaled.width(), 6)
                self.boxes[self.select_index][2] = round((self.select_box[2] + self.position[1]) / self.qimage_scaled.height(), 6)

                self.diff = [0, 0]
                self.disappear = False
                self.active_index = None
                self.active_box = None
                self.zoom_update()

            if self.flag_resize:
                self.flag_resize = False
                self.disappear = False

                self.boxes[self.select_index][1] = round((self.select_box[1] + self.position[0]) / self.qimage_scaled.width(), 6)
                self.boxes[self.select_index][2] = round((self.select_box[2] + self.position[1]) / self.qimage_scaled.height(), 6)
                self.boxes[self.select_index][3] = self.select_box[3] / self.qimage_scaled.width()
                self.boxes[self.select_index][4] = self.select_box[4] / self.qimage_scaled.height()
                self.zoom_update()

    # Mouse movement events
    def mouseMoveEvent(self, event):
        if self.connected:
            self.pos_x = event.x()
            self.pos_y = event.y()

            if self.indicator:
                self.update()

            if self.flag_zoom and (event.buttons() == Qt.RightButton or self.action_focus):
                if self.zoom_y > 1:
                    self.dx, self.dy = event.x() - self.move_x, event.y() - self.move_y
                    self.position = self.anchor[0] - self.dx, self.anchor[1] - self.dy
                    self.zoom_update()
            if self.flag:
                self.end_x = event.x()
                self.end_y = event.y()
                self.update()

            elif self.action_select and self.select_box and not self.priority:
                if 0 < sum(self.modify_box()) < 4:
                    self.focus_box()

                if event.buttons() == Qt.LeftButton:
                    if self.flag_carry:
                        self.diff = event.x() - self.past_x, event.y() - self.past_y

                        self.past_x, self.past_y = event.x(), event.y()

                        x = self.select_box[1] + self.diff[0]
                        y = self.select_box[2] + self.diff[1]
                        w = self.select_box[3]
                        h = self.select_box[4]
                        x, y = self.check_move_box(x, y, w, h)
                        self.select_box[1] = x
                        self.select_box[2] = y

                    if self.flag_resize:
                        self.resize_box()

                    if not self.disappear:
                        self.disappear = True
                        self.zoom_update()
                    self.update()
            else:
                if not self.priority:
                    self.focus_box()

    # Draw events
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.connected:
            if self.indicator:
                try:
                    painter = QPainter(self)
                    painter.setPen(QPen(Qt.red, 2))
                    painter.drawLine(0, self.pos_y, self.width(), self.pos_y)
                    painter.drawLine(self.pos_x, 0, self.pos_x, self.height())
                    painter.end()
                except:
                    pass
            if self.flag_resize or self.flag_carry:
                try:
                    painter = QPainter(self)

                    name = self.label_list[self.select_box[0]]
                    x = self.select_box[1]
                    y = self.select_box[2]
                    w = self.select_box[3]
                    h = self.select_box[4]

                    painter.setPen(QPen(QColor(self.color_selected_box), self.thickness + 5))
                    painter.drawPoint(x, y)
                    painter.drawPoint(x, y + h // 2)
                    painter.drawPoint(x, y + h)

                    painter.drawPoint(x + w // 2, y)
                    painter.drawPoint(x + w // 2, y + h)

                    painter.drawPoint(x + w, y)
                    painter.drawPoint(x + w, y + h//2)
                    painter.drawPoint(x + w, y + h)

                    painter.setFont(QFont("Verdana", 11))
                    painter.drawText(x, y - 5, name)

                    painter.setPen(QPen(QColor(self.color_selected_box), self.thickness, Qt.SolidLine))
                    painter.drawRect(x, y, w, h)
                    painter.end()
                except:
                    pass
            elif self.active_box:
                painter = QPainter(self)

                x = self.active_box[1]
                y = self.active_box[2]
                w = self.active_box[3]
                h = self.active_box[4]

                painter.setPen(QPen(QColor(self.color_selected_box), self.thickness, Qt.SolidLine))
                painter.drawRect(x, y, w, h)
                painter.end()

            if self.flag:
                self.x, self.y = self.st_x, self.st_y
                if self.end_x < self.st_x:
                    self.x = self.end_x
                    self.end_x = self.st_x

                if self.end_y < self.st_y:
                    self.y = self.end_y
                    self.end_y = self.st_y

                rect = QRect(self.x, self.y, self.end_x - self.x, self.end_y - self.y)
                painter = QPainter(self)
                painter.setPen(QPen(QColor(self.colors[self.color_idx]), self.thickness, Qt.SolidLine))

                painter.drawRect(rect)
                painter.end()

            if self.action_restrict_area:
                painter = QPainter(self)
                try:
                    poly = self.map_point_to_polygon(self.poly)

                    painter.setOpacity(0.7)
                    painter.setBrush(QBrush(Qt.black))
                    painter.setPen(QPen(Qt.black, 3, Qt.DashLine))
                    points = QPolygon(poly)
                    painter.drawPolygon(points)
                    painter.setPen(QPen(QColor('#B82647'), 6, Qt.SolidLine))
                    for p in poly:
                        painter.drawPoint(p)
                except:
                    pass
                painter.end()
