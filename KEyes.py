#!/usr/bin/env python

import os
import sys
import math
import random

from PyQt5.QtCore    import Qt
from PyQt5.QtCore    import QTimer
from PyQt5.QtCore    import QRectF
from PyQt5.QtCore    import QSizeF
from PyQt5.QtCore    import QPoint
from PyQt5.QtCore    import QPointF
from PyQt5.QtCore    import QRectF
from PyQt5.QtGui     import QIcon
from PyQt5.QtGui     import QColor
from PyQt5.QtGui     import QPainter
from PyQt5.QtGui     import QCursor
from PyQt5.QtGui     import QPixmap
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QApplication


def normalize_path(path):

  base_path = sys.path[0]

  if not base_path:
    base_path = os.getcwd()

  return os.path.join(base_path, path)


class Eye:

  pupil_size      = QSizeF(5, 5)
  eyesight_radius = 100.0


  def __init__(self, x, y, w, h):

    ## x, y are the coordinates of the center of the eye.
    ## w, h are the total width and height of the eye.

    self.size = QSizeF(w, h)
    self.pos  = QPointF(x, y)


  def toPointF(self, size):

    return QPointF(size.width(), size.height())


  def render(self, widget):

    painter = widget.painter

    if not painter:
      return

    previousRenderHint = painter.renderHints()
    painter.setRenderHints(previousRenderHint | QPainter.Antialiasing)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(253, 242, 245))

    painter.drawEllipse(QRectF(self.pos - self.toPointF(self.size/2), self.size))

    mouseOffset = QPointF(widget.mousePosition) \
                  - self.pos \
                  - QPointF(widget.frameGeometry().topLeft())

    ox, oy = mouseOffset.x(), mouseOffset.y()
    distance = math.sqrt(ox**2 + oy**2)

    if distance > self.eyesight_radius:
      ox *= self.eyesight_radius / distance
      oy *= self.eyesight_radius / distance

    px = self.pos.x() + ox/self.eyesight_radius * (self.size-self.pupil_size).width() / 2
    py = self.pos.y() + oy/self.eyesight_radius * (self.size-self.pupil_size).height() / 2

    pos = QPointF(px, py)

    painter.setBrush(Qt.black)
    painter.drawEllipse(QRectF(pos - self.toPointF(self.pupil_size/2), self.pupil_size))

    painter.setRenderHints(previousRenderHint)


class KEyesWidget(QWidget):

  update_interval = 50 # ms

  faces = {
    "Aaron":     ("keyes-aaron.png",     (49, 63, 12, 8), (79, 63, 12, 8)),
    "Adrian":    ("keyes-adrian.png",    (46, 67, 11, 6), (74, 68, 11, 6)),
    "Cornelius": ("keyes-cornelius.png", (49, 68, 11, 6), (79, 68, 11, 6)),
    "Eva":       ("keyes-eva.png",       (51, 63, 12, 6), (83, 63, 12, 6)),
    "Sebastian": ("keyes-sebastian.png", (50, 58, 14, 7), (83, 58, 14, 7)),
  }


  def __init__(self):

    QLabel.__init__(self)

    self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
    self.setAttribute(Qt.WA_NoSystemBackground)
    self.setMouseTracking(True)

    self.dragPosition  = QPoint(0, 0)
    self.mousePosition = QCursor.pos()

    self.actionFaces = QActionGroup(self)
    allFaceActions   = []

    for name in sorted(self.faces):

      action = QAction(name, self.actionFaces)
      action.setCheckable(True)
      allFaceActions.append(action)

    self.actionFaces.triggered.connect(self.actionUpdateFace)

    startAction = random.choice(allFaceActions)
    startAction.setChecked(True)
    self.actionUpdateFace(startAction)

    self.actionQuit = QAction("Quit", self)
    self.actionQuit.triggered.connect(QApplication.instance().quit)

    self.timer = QTimer()
    self.timer.timeout.connect(self.updateFromMousePosition)

    self.timer.start(self.update_interval)

    self.painter = None


  def actionUpdateFace(self, action):

    self.setFace(action.text())


  def setFace(self, name):

    self.setWindowTitle(name)
    self.pixmap = QPixmap(normalize_path(self.faces[name][0]))

    self.setWindowIcon(QIcon(self.pixmap))

    self.eyes = [Eye(*self.faces[name][1]), Eye(*self.faces[name][2])]

    self.setMask(self.pixmap.createHeuristicMask())

    if self.isVisible():
      self.update()


  def updateFromMousePosition(self):

    newPosition = QCursor.pos()

    if newPosition == self.mousePosition:
      return

    self.mousePosition = newPosition

    if self.isVisible():
      self.update()


  def mousePressEvent(self, event):

    if event.button() == Qt.LeftButton:

      self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()
      event.accept()


  def mouseMoveEvent(self, event):

    if event.buttons() == Qt.LeftButton:

      self.move(event.globalPos() - self.dragPosition)
      event.accept()


  def contextMenuEvent(self, event):

    menu = QMenu(self)

    menu.addActions(self.actionFaces.actions())
    menu.addSeparator()
    menu.addAction(self.actionQuit)

    menu.exec_(event.globalPos())


  def paintEvent(self, event):

    painter      = QPainter(self)
    self.painter = painter

    painter.drawPixmap(QPoint(0, 0), self.pixmap)

    for eye in self.eyes:
      eye.render(self)

    self.painter = None


  def sizeHint(self):

    return self.pixmap.size()




class KEyesApplication(QApplication):

  def __init__(self, argv=[]):

    QApplication.__init__(self, argv)
    self.widget = KEyesWidget()


  def run(self):

    self.widget.show()
    return self.exec_()




KEyesApplication(sys.argv).run()

