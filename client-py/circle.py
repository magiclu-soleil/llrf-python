import pyqtgraph as pg
import numpy as np
import math
from pyqtgraph.Qt import QtCore, QtGui

class Graph(pg.GraphItem):
    def __init__(self):
        ...


# Construct a unit radius circle for the graph
class EllipseObject(QtGui.QGraphicsObject):
    sigClicked = QtCore.pyqtSignal(float, float)
    def __init__(self, center= (0.0, 0.0), radius=1.0, pen=QtGui.QPen(QtCore.Qt.white)):
        QtGui.QGraphicsObject.__init__(self)
        self.center = center
        self.radius = radius
        self.pen = pen

    def boundingRect(self):
        rect = QtCore.QRectF(0, 0, 2*self.radius, 2*self.radius)
        rect.moveCenter(QtCore.QPointF(*self.center))
        return rect

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.drawEllipse(self.boundingRect())

    def mousePressEvent(self, event):
        p = event.pos()
        self.sigClicked.emit(p.x(), p.y())
        QtGui.QGraphicsEllipseItem.mousePressEvent(self, event)

if __name__ == '__main__':
    position = [(-0.5,0), (0.5,0)]
    adjacency = [(0,1)]
    w = pg.GraphicsWindow()
    w.setWindowTitle('Title of the window')
    v = w.addViewBox()
    v.setAspectLocked()
    g = Graph()
    v.addItem(g)

    g.setData(pos=np.array(position), adj=np.array(adjacency), pxMode=False, size=0.1)
    item = EllipseObject()
    item.sigClicked.connect(lambda x, y: print(x, y))
    v.addItem(item)

    import sys

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
