#!/usr/bin/env python

import math
import random
import sys

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

import resources

del resources


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
            QRectF(self.pos - self.toPointF(self.size / 2), self.size)
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
            QRectF(pos - self.toPointF(self.pupil_size / 2), self.pupil_size)
        )

        painter.setRenderHints(previousRenderHint)


class KEyesWidget(QWidget):
    update_interval = 50  # ms

    faces = {
        "Aaron": (
            ":resources/aaron.png",
            (49, 63, 12, 8),
            (79, 63, 12, 8),
        ),
        "Adrian": (
            ":resources/adrian.png",
            (46, 67, 11, 6),
            (74, 68, 11, 6),
        ),
        "Cornelius": (
            ":resources/cornelius.png",
            (49, 68, 11, 6),
            (79, 68, 11, 6),
        ),
        "Eva": (":resources/eva.png", (51, 63, 12, 6), (83, 63, 12, 6)),
        "Sebastian": (
            ":resources/sebastian.png",
            (50, 58, 14, 7),
            (83, 58, 14, 7),
        ),
    }

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
        allFaceActions: list[QAction] = []

        for name in sorted(self.faces):
            action = QAction(name, self.actionFaces)
            action.setCheckable(True)
            allFaceActions.append(action)

        self.actionFaces.triggered.connect(self.actionUpdateFace)

        startAction = random.choice(allFaceActions)
        startAction.setChecked(True)
        self.actionUpdateFace(startAction)

        timer = QTimer(self)
        timer.timeout.connect(self.updateFromMousePosition)

        timer.start(self.update_interval)

    def actionUpdateFace(self, action: QAction) -> None:
        self.setFace(action.text())

    def setFace(self, name: str) -> None:
        self.setWindowTitle(name)
        self.pixmap = QPixmap(self.faces[name][0])

        self.setWindowIcon(QIcon(self.pixmap))

        self.eyes = [Eye(*self.faces[name][1]), Eye(*self.faces[name][2])]

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = KEyesWidget()
    widget.show()
    app.exec()
