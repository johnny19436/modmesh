# Copyright (c) 2018, Yung-Yu Chen <yyc@solvcon.net>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# - Neither the name of the copyright holder nor the names of its contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import numpy as np

from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qtagg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

from .. import pilot
from .. import spacetime as libst


def load_app():
    cmd = "win, svr = mm.onedim.linear_wave.run_linear(animate=True, " \
          "interval=10)"
    pilot.mgr.pycon.command = cmd


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        self.canvas = FigureCanvas(Figure(figsize=(15, 10)))
        # Ideally one would use self.addToolBar here, but it is slightly
        # incompatible between PyQt6 and other bindings, so we just add the
        # toolbar as a plain widget instead.
        layout.addWidget(self.canvas)
        layout.addWidget(NavigationToolbar(self.canvas, self))

        self.svr = None
        self.ax = self.canvas.figure.subplots()
        self.timer = None
        self.line = None

    def set_solver(self, svr, interval):
        """
        :param svr: Solver
        :param interval: milliseconds
        :return: nothing
        """
        self.svr = svr
        x = svr.xctr() / np.pi
        y = svr.get_so0(0).ndarray
        self.line, = self.ax.plot(x, y, '-')
        self.timer = self.canvas.new_timer(interval)
        self.timer.add_callback(self._update_canvas)
        self.timer.start()

    def _update_canvas(self):
        self.svr.march_alpha2(1)
        self.line.set_data(self.svr.xctr() / np.pi,
                           self.svr.get_so0(0).ndarray)
        self.line.figure.canvas.draw()


def run_linear(animate, interval=10):
    grid = libst.Grid(0, 4 * 2 * np.pi, 4 * 64)

    cfl = 1
    dx = (grid.xmax - grid.xmin) / grid.ncelm
    dt = dx * cfl
    svr = libst.LinearScalarSolver(grid=grid, time_increment=dt)

    # Initialize
    for e in svr.selms(odd_plane=False):
        if e.xctr < 2 * np.pi or e.xctr > 2 * 2 * np.pi:
            v = 0
            dv = 0
        else:
            v = np.sin(e.xctr)
            dv = np.cos(e.xctr)
        e.set_so0(0, v)
        e.set_so1(0, dv)

    win = ApplicationWindow()
    win.show()
    win.activateWindow()

    svr.setup_march()

    if animate:
        win.set_solver(svr, interval)
    else:
        win.ax.plot(svr.xctr() / np.pi, svr.get_so0(0).ndarray, '-')
        svr.march_alpha2(50)
        win.ax.plot(svr.xctr() / np.pi, svr.get_so0(0).ndarray, '-')

    return win, svr

# vim: set ff=unix fenc=utf8 et sw=4 ts=4 sts=4:
