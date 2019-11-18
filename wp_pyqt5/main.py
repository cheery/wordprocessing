#!/usr/bin/env python3
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QPointF, QRect
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QLabel
from piecetable import PieceTable
import importlib # For importlib.reload
import paint_qt5
import minitex
import view
import sys
import math

def main():
    app = QApplication(sys.argv)
    main = MainWindow(None)
    app.setActiveWindow(main)
    main.show()
    sys.exit(app.exec_())

class MainWindow(QMainWindow):
    def __init__(self, parent):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle("wp")
        self.menu = self.menuBar()
        #test = menu.addMenu("Test")
        self.editor = EditorFrame(self)
        self.setCentralWidget(self.editor)
        self.setGeometry(100, 100, #1800, 900)
            self.editor.prefered_width,
            self.editor.prefered_height)

        # TODO: Figure out the status bar later.
        #self.status = self.statusBar()
        #status_left = QLabel(self.status)
        #status_left.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        #status_right = QLabel(self.status)
        #status_right.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        #self.status.addPermanentWidget(status_left, 1)
        #self.status.addPermanentWidget(status_right, 1)
        #status_left.setText("LEFT")
        #status_right.setText("RIGHT")

    #def closeEvent(self, event):
    #    print("actions on close")
    #    event.accept()

class EditorFrame(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setCursor(Qt.IBeamCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.frame_width = 0
        self.frame_height = 0
        self.rootbox = None

        self.filename = "../sample_text.wp"
        with open(self.filename, 'r', encoding='utf-8') as fd:
            self.buffer = PieceTable(fd.read())

        self.par_font = QtGui.QFont('Sans Serif', 24)
        self.par_raw = QtGui.QRawFont.fromFont(self.par_font)

        self.mono_font = QtGui.QFont('Monospace', 24)
        self.mono_raw = QtGui.QRawFont.fromFont(self.mono_font)
        self.mono_metrics = QtGui.QFontMetrics(self.mono_font)
        self.prefered_width = self.mono_metrics.averageCharWidth() * 80
        self.prefered_height = self.mono_metrics.lineSpacing() * 24

        self.setStyleSheet("background-color:#ffffdd")
        self.debug = False
        self.display_plain = False

        self.cursor = 0
        self.y_scroll = 0

        import os.path
        self.view_mtime = os.path.getmtime("view.py")
        self.view_recheck = QtCore.QTimer(self)
        self.view_recheck.timeout.connect(self.recheckEvent)
        self.view_recheck.start(1000)
        self.selections = []

    def recheckEvent(self):
        import os.path
        try:
            view_mtime = os.path.getmtime("view.py")
        except FileNotFoundError as _:
            pass
        else:
            if self.view_mtime < view_mtime:
                self.view_mtime = view_mtime
                importlib.reload(view)
                self.relayout()

    def resizeEvent(self, e):
        self.frame_width = e.size().width()
        self.frame_height = e.size().height()
        self.relayout()

    def relayout(self):
        if self.frame_width == 0 or self.frame_height == 0:
            return
        if self.display_plain:
            self.rootbox = view.plaintext_display(self.buffer,
                self.mono_raw)
        else:
            self.rootbox = view.full_display(self.buffer,
                self.mono_raw, self.par_raw, self.getfont)

    def getfont(self, size):
        font = QtGui.QFont("Sans Serif", size)
        return QtGui.QRawFont.fromFont(font)

    def wheelEvent(self, e):
        self.y_scroll -= e.angleDelta().y()  # +-120
        self.y_scroll = max(self.y_scroll, 0)
        self.update()

    def mousePressEvent(self, e):
        mouse_x = e.x()
        mouse_y = e.y()
        def min_key(item):
            (x,y,frame) = item
            ix = max(min(mouse_x, x + frame.width), x)
            iy = max(min(mouse_y, y + frame.depth), y - frame.height)
            dy = abs(iy-mouse_y)
            dx = abs(ix-mouse_x)
            return (dy, dx)
        x,y,best = min([(x,y,frame)
             for seltype,x,y,frame in self.selections
             if seltype == "rawtext"], key=min_key)
        def min_off(item):
            (offset, pt) = item
            return abs(mouse_x-x-pt.x())
        best_pos, _ = min(
            enumerate(best.paint.positions, best.paint.offset),
            key=min_off)
        self.cursor = best_pos
        self.update()

#    def mouseMoveEvent(self, e):
#        self.update()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_F3:
            self.display_plain = not self.display_plain
            self.relayout()
            self.update()
        # Temporary key to allow file to be saved.
        elif e.key() == QtCore.Qt.Key_F2:
            with open(self.filename, 'w', encoding='utf-8') as fd:
                for text in self.buffer.peek(0, self.buffer.length):
                    fd.write(text)
        #elif e.key() == Qt.Key_Escape:
        #    self.parent().close()
        elif e.key() == QtCore.Qt.Key_Backspace:
            if self.cursor > 0:
                self.cursor -= 1
                self.buffer.delete(self.cursor, length=1)
                self.relayout()
                self.update()
        elif e.key() == QtCore.Qt.Key_Delete:
            if self.buffer.length > self.cursor:
                self.buffer.delete(self.cursor, length=1)
                self.relayout()
                self.update()
        elif e.key() == QtCore.Qt.Key_Left:
            if self.cursor > 0:
                self.cursor -= 1
                self.relayout()
                self.update()
        elif e.key() == QtCore.Qt.Key_Right:
            if self.cursor < self.buffer.length:
                self.cursor += 1
                self.relayout()
                self.update()
        elif e.key() == QtCore.Qt.Key_Up:
            ncursor = lookabove(self.cursor, self.selections)
            if ncursor is not None:
                self.cursor = ncursor
                self.update()
        elif e.key() == QtCore.Qt.Key_Down:
            ncursor = lookbelow(self.cursor, self.selections)
            if ncursor is not None:
                self.cursor = ncursor
                self.update()
        elif e.key() == QtCore.Qt.Key_Return:
            self.buffer.insert(self.cursor, '\n')
            self.cursor += len('\n')
            self.relayout()
            self.update()
        else:
            text = e.text()
            self.buffer.insert(self.cursor, text)
            self.cursor += len(text)
            self.relayout()
            self.update()

        #mod = e.modifiers()
        #modprefix = ""
        #if int(mod & Qt.ControlModifier) != 0:
        #    modprefix += "c-"
        #if int(mod & Qt.AltModifier) != 0:
        #    modprefix += "a-"
        #if int(mod & Qt.ShiftModifier) != 0:
        #    modprefix += "s-"
        #pattern = "<" + modprefix + "{}>"
        ## Get root key name.
        ## Wrap into brackets if special.
        ## Wrap shift_mod if special key
        ## Wrap into brackets if modded.
        #elif e.key() == QtCore.Qt.Key_Home:
        #    self.kak_send('keys', pattern.format('home'))
        #elif e.key() == QtCore.Qt.Key_End:
        #    self.kak_send('keys', pattern.format('end'))
        #elif e.key() == QtCore.Qt.Key_Tab:
        #    self.kak_send('keys', pattern.format('tab'))
        #elif e.key() == QtCore.Qt.Key_Tab+1: # Lol wtf Qt.
        #    self.kak_send('keys', pattern.format('tab'))
        #elif e.key() == QtCore.Qt.Key_Return:
        #    self.kak_send('keys', pattern.format('ret'))
        #elif e.key() == QtCore.Qt.Key_PageUp:
        #    self.kak_send('keys', pattern.format('pageup'))
        #elif e.key() == QtCore.Qt.Key_PageDown:
        #    self.kak_send('keys', pattern.format('pagedown'))
        #else:
        #    modprefix = modprefix.replace("s-", "")
        #    keys = []
        #    for ch in str(e.text()):
        #        if ord(ch) < 0x20:
        #            # http://www.physics.udel.edu/~watson/scen103/ascii.html
        #            ch = chr(ord(ch) + 0x60)
        #            key = ch
        #            if len(modprefix) > 0:
        #                key = pattern.format(ch)
        #        else:
        #            key = ch
        #            if len(modprefix) > 0:
        #                key = pattern.replace("s-", "").format(ch)
        #        keys.append(key)
        #    self.kak_send('keys', *keys)

    def paintEvent(self, event):
        QFrame.paintEvent(self, event)
        selections = []
        paint = QtGui.QPainter()
        paint.begin(self)
        x = 2
        y = 2 + self.rootbox.height - self.y_scroll
        self.compose(paint, selections, self.rootbox, x, y,
            2, 2, self.rootbox.width, y+self.rootbox.depth)
        # The selection drawing routine.
        for seltype,x,y,frame in selections:
            if seltype == "rawtext":
                start = frame.paint.offset
                stop = start + len(frame.paint.positions)
                if start <= self.cursor < stop:
                    k = self.cursor - start
                    positions = frame.paint.positions
                    px = x + positions[k].x()
                    py = y + positions[k].y()
                    top = y - frame.height
                    paint.drawRect(QRect(px, top, 2, frame.height+frame.depth))
        self.selections = selections
#       code to draw the selection.
#       paint.fillRect(QRectF(x1, 3 + y1 * self.fontht, x2-x1, self.fontht), QColor(0,0,255,100))
        paint.end()

    def compose(self,paint,selections,frame,x,y,left,top,right,bottom):
        if self.debug:
            paint.drawRect(QRect(left, top, right-left, bottom-top))
        if frame.paint:
            frame.paint.draw(paint,frame,x,y,left,top,right,bottom)
            if isinstance(frame.paint, paint_qt5.RawText):
                selections.append(('rawtext',x,y,frame))
        if self.debug and isinstance(frame, minitex.Box):
            #pen = paint.pen()
            #paint.setPen(self.linkpen)
            paint.drawRect(QRect(x, y-frame.height, frame.width, frame.height+frame.depth))
            #paint.setPen(pen)
        if isinstance(frame, minitex.Frame):
            for args in frame.layout(frame,x,y,left,top,right,bottom):
                self.compose(paint, selections, *args)

def lookabove(cursor, selections):
    for sx,sy in find_screen_positions(cursor, selections):
        return lookabove_point((sx,sy), selections)
    return None

def lookabove_point(sxy, selections):
    (sx,sy) = sxy
    def min_key(item):
        (x,y,frame) = item
        ix = max(min(sx, x + frame.width), x)
        iy = max(min(sy + 5, y + frame.depth), y - frame.height)
        dx = ix-sx
        dy = iy-sy
        l = math.sqrt(dx*dx + dy*dy)
        if l == 0:
            z = 1
        else:
            z = 1 + (dy/l)
        return (z, l)
    x,y,best = min([(x,y,frame)
         for seltype,x,y,frame in selections
         if seltype == "rawtext"], key=min_key)
    def min_off(item):
        (offset, pt) = item
        return abs(sx-x-pt.x())
    best_pos, _ = min(
        enumerate(best.paint.positions, best.paint.offset),
        key=min_off)
    return best_pos

def lookbelow(cursor, selections):
    for sx,sy in find_screen_positions(cursor, selections):
        return lookbelow_point((sx,sy), selections)
    return None

def lookbelow_point(sxy, selections):
    (sx,sy) = sxy
    def min_key(item):
        (x,y,frame) = item
        ix = max(min(sx, x + frame.width), x)
        iy = max(min(sy - 5, y + frame.depth), y - frame.height)
        dx = ix-sx
        dy = iy-sy
        l = math.sqrt(dx*dx + dy*dy)
        if l == 0:
            z = 1
        else:
            z = 1 - (dy/l)
        return z
    x,y,best = min([(x,y,frame)
         for seltype,x,y,frame in selections
         if seltype == "rawtext"], key=min_key)
    def min_off(item):
        (offset, pt) = item
        return abs(sx-x-pt.x())
    best_pos, _ = min(
        enumerate(best.paint.positions, best.paint.offset),
        key=min_off)
    return best_pos

def find_screen_positions(cursor, selections):
    points = [getmap(cursor,x,y,frame)
        for seltype,x,y,frame in selections
        if seltype == "rawtext"
        and 0 <= (cursor - frame.paint.offset) < len(frame.paint.positions)]
    return points

def getmap(cursor, x, y, frame):
    pt = frame.paint.positions[cursor - frame.paint.offset]
    return (x+pt.x(), y+pt.y())

if __name__=='__main__':
    main()
