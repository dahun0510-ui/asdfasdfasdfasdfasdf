# === Standard Library Imports ===
import logging
from typing import Optional, Tuple

# === Third-Party Imports ===
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QFrame, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QPixmap, QPainter

# === Local Imports ===
# config import는 필요시 추가

class ScanGuide(QWidget):
    """스캔 가이드 위젯"""

    guide_updated = pyqtSignal(dict)  # 가이드 영역 업데이트 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.guide_areas = {}  # 가이드 영역들
        self.current_screenshot = None
        self.is_editing = False
        self.selected_area = None

        self.initUI()
        self.load_default_areas()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 제목
        title = QLabel("스캔 가이드 설정")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # 그래픽스 뷰
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        self.graphics_view.setMinimumHeight(300)
        self.graphics_view.setStyleSheet("border: 1px solid #BDC3C7;")

        layout.addWidget(self.graphics_view)

        # 컨트롤 버튼들
        controls_layout = QHBoxLayout()

        self.add_button = QPushButton("영역 추가")
        self.add_button.clicked.connect(self.add_guide_area)
        controls_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("편집 모드")
        self.edit_button.setCheckable(True)
        self.edit_button.clicked.connect(self.toggle_edit_mode)
        controls_layout.addWidget(self.edit_button)

        self.clear_button = QPushButton("모두 삭제")
        self.clear_button.clicked.connect(self.clear_all_areas)
        controls_layout.addWidget(self.clear_button)

        self.save_button = QPushButton("저장")
        self.save_button.clicked.connect(self.save_areas)
        controls_layout.addWidget(self.save_button)

        layout.addLayout(controls_layout)

        # 상태 라벨
        self.status_label = QLabel("편집 모드를 활성화하여 영역을 설정하세요.")
        self.status_label.setStyleSheet("color: #7F8C8D; font-size: 12px;")
        layout.addWidget(self.status_label)

    def load_default_areas(self):
        """기본 가이드 영역 로드"""
        # 기본 포커 플레이어 영역들
        default_areas = {
            "player1": {"x": 100, "y": 100, "width": 150, "height": 50, "label": "Player 1"},
            "player2": {"x": 300, "y": 100, "width": 150, "height": 50, "label": "Player 2"},
            "player3": {"x": 500, "y": 100, "width": 150, "height": 50, "label": "Player 3"},
            "player4": {"x": 100, "y": 300, "width": 150, "height": 50, "label": "Player 4"},
            "player5": {"x": 300, "y": 300, "width": 150, "height": 50, "label": "Player 5"},
            "player6": {"x": 500, "y": 300, "width": 150, "height": 50, "label": "Player 6"},
        }

        for area_id, area_data in default_areas.items():
            self.add_guide_area_from_data(area_id, area_data)

    def add_guide_area(self):
        """새 가이드 영역 추가"""
        area_id = f"area_{len(self.guide_areas) + 1}"
        area_data = {
            "x": 50,
            "y": 50,
            "width": 120,
            "height": 40,
            "label": f"Area {len(self.guide_areas) + 1}"
        }
        self.add_guide_area_from_data(area_id, area_data)

    def add_guide_area_from_data(self, area_id: str, area_data: dict):
        """데이터로부터 가이드 영역 추가"""
        # 그래픽스 아이템 생성
        rect_item = ResizableRectItem(
            area_data["x"], area_data["y"],
            area_data["width"], area_data["height"]
        )
        rect_item.set_label(area_data["label"])
        rect_item.area_id = area_id

        # 시그널 연결
        rect_item.geometry_changed.connect(self.on_area_geometry_changed)
        rect_item.selected.connect(self.on_area_selected)

        self.scene.addItem(rect_item)
        self.guide_areas[area_id] = {
            "item": rect_item,
            "data": area_data
        }

        self.update_status()

    def toggle_edit_mode(self, checked: bool):
        """편집 모드 토글"""
        self.is_editing = checked

        for area_data in self.guide_areas.values():
            area_data["item"].set_editable(checked)

        if checked:
            self.status_label.setText("영역을 드래그하여 이동시키고, 코너를 드래그하여 크기를 조절하세요.")
        else:
            self.status_label.setText("편집 모드를 활성화하여 영역을 설정하세요.")

    def clear_all_areas(self):
        """모든 영역 삭제"""
        for area_data in self.guide_areas.values():
            self.scene.removeItem(area_data["item"])

        self.guide_areas.clear()
        self.update_status()

    def save_areas(self):
        """영역 저장"""
        areas_data = {}
        for area_id, area_data in self.guide_areas.items():
            item = area_data["item"]
            rect = item.rect()
            areas_data[area_id] = {
                "x": int(rect.x()),
                "y": int(rect.y()),
                "width": int(rect.width()),
                "height": int(rect.height()),
                "label": item.get_label()
            }

        # 시그널 발생
        self.guide_updated.emit(areas_data)
        self.status_label.setText(f"영역 설정이 저장되었습니다. ({len(areas_data)}개 영역)")

    def on_area_geometry_changed(self, area_id: str, rect: QRectF):
        """영역 지오메트리 변경 처리"""
        if area_id in self.guide_areas:
            self.guide_areas[area_id]["data"].update({
                "x": int(rect.x()),
                "y": int(rect.y()),
                "width": int(rect.width()),
                "height": int(rect.height())
            })

    def on_area_selected(self, area_id: str):
        """영역 선택 처리"""
        self.selected_area = area_id

        # 다른 영역들 선택 해제
        for aid, area_data in self.guide_areas.items():
            if aid != area_id:
                area_data["item"].set_selected(False)

    def update_screenshot(self, pixmap: QPixmap):
        """스크린샷 업데이트"""
        self.current_screenshot = pixmap

        # 기존 배경 제거
        for item in self.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                self.scene.removeItem(item)

        # 새 스크린샷 추가
        if pixmap:
            pixmap_item = self.scene.addPixmap(pixmap)
            pixmap_item.setZValue(-1)  # 뒤로 보내기

            # 씬 크기 조정
            self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())

    def get_areas_data(self) -> dict:
        """영역 데이터 반환"""
        areas_data = {}
        for area_id, area_data in self.guide_areas.items():
            item = area_data["item"]
            rect = item.rect()
            areas_data[area_id] = {
                "x": int(rect.x()),
                "y": int(rect.y()),
                "width": int(rect.width()),
                "height": int(rect.height()),
                "label": item.get_label()
            }
        return areas_data

    def update_status(self):
        """상태 업데이트"""
        area_count = len(self.guide_areas)
        if self.is_editing:
            self.status_label.setText(f"편집 모드 활성화 - {area_count}개 영역")
        else:
            self.status_label.setText(f"영역 개수: {area_count}")


class ResizableRectItem(QGraphicsRectItem):
    """크기 조절 가능한 사각형 아이템"""

    geometry_changed = pyqtSignal(str, QRectF)  # area_id, rect
    selected = pyqtSignal(str)  # area_id

    def __init__(self, x: float, y: float, width: float, height: float):
        super().__init__(x, y, width, height)
        self.area_id = ""
        self.label_text = ""
        self.is_editable = False
        self.is_selected = False

        # 핸들 크기
        self.handle_size = 8

        # 펜과 브러시 설정
        self.normal_pen = QPen(QColor("#3498DB"), 2)
        self.selected_pen = QPen(QColor("#E74C3C"), 3)
        self.normal_brush = QBrush(QColor(52, 152, 219, 100))
        self.selected_brush = QBrush(QColor(231, 76, 60, 150))

        self.setPen(self.normal_pen)
        self.setBrush(self.normal_brush)

        # 텍스트 아이템
        self.text_item = QGraphicsTextItem("", self)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.white)
        self.text_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.update_text_position()

        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def set_label(self, label: str):
        """라벨 설정"""
        self.label_text = label
        self.text_item.setPlainText(label)
        self.update_text_position()

    def get_label(self) -> str:
        """라벨 반환"""
        return self.label_text

    def set_editable(self, editable: bool):
        """편집 가능 여부 설정"""
        self.is_editable = editable
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, editable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, editable)

    def set_selected(self, selected: bool):
        """선택 상태 설정"""
        self.is_selected = selected
        if selected:
            self.setPen(self.selected_pen)
            self.setBrush(self.selected_brush)
            self.selected.emit(self.area_id)
        else:
            self.setPen(self.normal_pen)
            self.setBrush(self.normal_brush)

    def update_text_position(self):
        """텍스트 위치 업데이트"""
        rect = self.rect()
        text_rect = self.text_item.boundingRect()
        center_x = rect.x() + (rect.width() - text_rect.width()) / 2
        center_y = rect.y() + (rect.height() - text_rect.height()) / 2
        self.text_item.setPos(center_x, center_y)

    def itemChange(self, change, value):
        """아이템 변경 처리"""
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange:
            if self.area_id:
                self.geometry_changed.emit(self.area_id, self.rect())
        elif change == QGraphicsRectItem.GraphicsItemChange.ItemSelectedChange:
            self.set_selected(bool(value))

        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if self.is_editable:
            super().mousePressEvent(event)
            self.set_selected(True)
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        if self.is_editable:
            super().mouseMoveEvent(event)
            self.update_text_position()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        """마우스 해제 이벤트"""
        if self.is_editable:
            super().mouseReleaseEvent(event)
            if self.area_id:
                self.geometry_changed.emit(self.area_id, self.rect())
        else:
            event.ignore()