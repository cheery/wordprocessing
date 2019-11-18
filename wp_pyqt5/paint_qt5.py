from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QPointF, QRect
from minitex import Box
import minitex

def textbox(rawfont, text, offset, color=None):
    half_leading = rawfont.leading() / 2
    height = rawfont.ascent() + half_leading
    depth = rawfont.descent() + half_leading
    paint = RawText(rawfont, text, offset, color)
    return Box(paint.positions[-1].x(), height, depth, paint)

def width_of(rawfont, text):
    indexes = rawfont.glyphIndexesForString(text)
    positions = position_text(rawfont, indexes)
    return positions[-1].x()

class RawText(object):
    def __init__(self, rawfont, text, offset, color):
        self.offset = offset
        self.indexes = rawfont.glyphIndexesForString(text)
        self.positions = position_text(rawfont, self.indexes)
        self.glyphrun = QtGui.QGlyphRun()
        self.glyphrun.setRawFont(rawfont)
        self.glyphrun.setGlyphIndexes(self.indexes)
        self.glyphrun.setPositions(self.positions)
        self.color = color

    def draw(self, paint, frame, x, y, left, top, right, bottom):
        if self.color is not None:
            pen = paint.pen()
            qpen = QtGui.QPen()
            qpen.setColor(QtGui.QColor(self.color))
            paint.setPen(qpen)
            paint.drawGlyphRun(QPointF(x, y), self.glyphrun)
            paint.setPen(pen)
        else:
            paint.drawGlyphRun(QPointF(x, y), self.glyphrun)

def position_text(rawfont, indexes):
    advances = rawfont.advancesForGlyphIndexes(indexes)
    x = 0
    y = 0
    positions = []
    for pt in advances:
        positions.append(QPointF(x, y))
        x += pt.x()
        y += pt.y()
    positions.append(QPointF(x, y))
    return positions

