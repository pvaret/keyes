#!/usr/bin/env python

import math
import random
import sys

from dataclasses import dataclass
from typing import NoReturn

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, QSizeF, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QContextMenuEvent,
    QCursor,
    QIcon,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QWidget,
)

from keyes import resources

del resources


@dataclass
class Face:
    name: str
    pixmap: str
    left_eye: tuple[int, int, int, int]
    right_eye: tuple[int, int, int, int]


class Eye:
    pupil_size = QSizeF(5, 5)
    eyesight_radius = 100.0

    size: QSizeF
    pos: QPointF

    def __init__(self, x: int, y: int, w: int, h: int) -> None:
        # x, y are the coordinates of the center of the eye.
        # w, h are the total width and height of the eye.

        self.size = QSizeF(w, h)
        self.pos = QPointF(x, y)

    def toPointF(self, size: QSizeF) -> QPointF:
        return QPointF(size.width(), size.height())

    def render(self, relativeMouseOffset: QPoint, painter: QPainter) -> None:
        previousRenderHint = painter.renderHints()
        painter.setRenderHints(
            previousRenderHint | QPainter.RenderHint.Antialiasing
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(253, 242, 245))

        painter.drawEllipse(
            QRectF(self.pos - self.toPointF(self.size / 2), self.size)  # type: ignore
        )

        mouseOffset = QPointF(relativeMouseOffset) - self.pos

        ox, oy = mouseOffset.x(), mouseOffset.y()
        distance = math.sqrt(ox**2 + oy**2)

        if distance > self.eyesight_radius:
            ox *= self.eyesight_radius / distance
            oy *= self.eyesight_radius / distance

        px = (
            self.pos.x()
            + ox
            / self.eyesight_radius
            * (self.size - self.pupil_size).width()
            / 2
        )
        py = (
            self.pos.y()
            + oy
            / self.eyesight_radius
            * (self.size - self.pupil_size).height()
            / 2
        )

        pos = QPointF(px, py)

        painter.setBrush(Qt.GlobalColor.black)
        painter.drawEllipse(
            QRectF(pos - self.toPointF(self.pupil_size / 2), self.pupil_size)  # type: ignore
        )

        painter.setRenderHints(previousRenderHint)


class KEyesWidget(QWidget):
    update_interval = 50  # ms

    faces = [
        Face(
            "Aaron",
            ":aaron.png",
            (49, 63, 12, 8),
            (79, 63, 12, 8),
        ),
        Face(
            "Adrian",
            ":adrian.png",
            (46, 67, 11, 6),
            (74, 68, 11, 6),
        ),
        Face(
            "Cornelius",
            ":cornelius.png",
            (49, 68, 11, 6),
            (79, 68, 11, 6),
        ),
        Face(
            "Eva",
            ":eva.png",
            (51, 63, 12, 6),
            (83, 63, 12, 6),
        ),
        Face(
            "Sebastian",
            ":sebastian.png",
            (50, 58, 14, 7),
            (83, 58, 14, 7),
        ),
    ]

    dragPosition: QPoint
    mousePosition: QPoint
    actionFaces: QActionGroup

    def __init__(self) -> None:
        super().__init__()

        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setMouseTracking(True)

        self.dragPosition = QPoint(0, 0)
        self.mousePosition = QCursor.pos()

        self.actionFaces = QActionGroup(self)

        for face in sorted(self.faces, key=lambda face: face.name):
            action = QAction(face.name, self.actionFaces)
            action.setCheckable(True)
            action.setData(face)

        self.actionFaces.triggered.connect(self.actionUpdateFace)

        startAction = random.choice(self.actionFaces.actions())
        startAction.setChecked(True)
        self.actionUpdateFace(startAction)

        timer = QTimer(self)
        timer.timeout.connect(self.updateFromMousePosition)

        timer.start(self.update_interval)

    def actionUpdateFace(self, action: QAction) -> None:
        face = action.data()
        match face:
            case Face():
                self.setFace(face)
            case _:
                pass

    def setFace(self, face: Face) -> None:
        self.setWindowTitle(face.name)
        self.pixmap = QPixmap(face.pixmap)

        self.setWindowIcon(QIcon(self.pixmap))

        self.eyes = [Eye(*face.left_eye), Eye(*face.right_eye)]

        self.setMask(self.pixmap.createHeuristicMask())

        if self.isVisible():
            self.update()

    def updateFromMousePosition(self) -> None:
        newPosition = QCursor.pos()

        if newPosition == self.mousePosition:
            return

        self.mousePosition = newPosition

        if self.isVisible():
            self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPosition = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.dragPosition)
            event.accept()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        menu = QMenu(self)

        menu.addActions(self.actionFaces.actions())
        menu.addSeparator()
        actionQuit = QAction("Quit")
        if (app := QApplication.instance()) is not None:
            actionQuit.triggered.connect(app.quit)

        menu.addAction(actionQuit)

        menu.exec(event.globalPos())

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)

        painter.drawPixmap(QPoint(0, 0), self.pixmap)
        mouseOffset = self.mousePosition - self.frameGeometry().topLeft()

        for eye in self.eyes:
            eye.render(mouseOffset, painter)

    def sizeHint(self) -> QSize:
        return self.pixmap.size()


def main() -> NoReturn:
    app = QApplication(sys.argv)
    widget = KEyesWidget()
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
