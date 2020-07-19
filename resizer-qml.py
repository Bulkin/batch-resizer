import sys
import os

from functools import reduce

from PyQt5.Qt import QApplication
from PyQt5.QtCore import QObject, QProcess
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import pyqtProperty, pyqtSignal, pyqtSlot

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)



class ImageMagickDispatcher(QObject):
    images_changed = pyqtSignal()
    scale_chaged = pyqtSignal()
    output_format_changed = pyqtSignal()
    tasks_finished = pyqtSignal()

    # task_map: process id -> image ref
    # image: { 'name': '/file/name',
    #          'output':'/output/file/name',
    #          'status':{'Waiting', 'Ok', Error message} }
    def __init__(self):
        super().__init__()
        self.im_binary = 'convert'
        self._images = []
        self._scale = 50.0
        self.output_format = '' # %p/%n-resized -- ext is added automatically
        self.images_changed.emit()
        self.process_pool = [QProcess() for i in range(4)] # parallelization
        self.task_map = {}
        for (i, p) in enumerate(self.process_pool):
            p.finished.connect(lambda exit_code, exit_status, i=i:
                               self.handle_process_finished(i, exit_code, exit_status))

    def make_command(self, img):
        command = [ self.im_binary,
                    img['name'],
                    '-resize',
                    str(self._scale) + '%',
                    img['output'],
        ]
        return command

    def grab_image_task(self, proc_id):
        unfinished_tasks = [ img for img in self._images
                             if img['status'] == 'Waiting'
                             and img not in self.task_map.values() ]
        if proc_id in self.task_map:
            del self.task_map[proc_id]
        if unfinished_tasks:
            img = unfinished_tasks[0]
            self.task_map[proc_id] = img
            cmd = self.make_command(img)
            self.process_pool[proc_id].start(cmd[0], cmd[1:])

        self.tasks_finished.emit()

    def handle_process_finished(self, id, exit_code, exit_status):
        print('Finished', id)
        img = self.task_map[id]
        img['status'] = ('Ok' if exit_code == 0 else
                         self.process_pool[id].readAllStandardOutput() +
                         self.process_pool[id].readAllStandardError())
        self.images_changed.emit()
        self.grab_image_task(id)

    def default_format(self, input_name):
        name, ext = os.path.splitext(os.path.basename(input_name))
        dir = os.path.dirname(input_name)
        return dir + '/%n-resized' + ext

    def format_output(self, input_name):
        name, ext = os.path.splitext(os.path.basename(input_name))
        dir = os.path.dirname(input_name)
        replace_table = { '%p': dir,
                          '%n': name,
        }
        return reduce(lambda s, kv: s.replace(kv[0], kv[1]),
                      replace_table.items(),
                      self.output_format)

    @pyqtSlot()
    def run(self):
        for id in range(len(self.process_pool)):
            self.grab_image_task(id)

    @pyqtSlot('QList<QUrl>')
    def add(self, names):
        if self.output_format == '':
            self.setOutputFormat(self.default_format(names[0].toLocalFile()))

        self._images += [ { 'name' : n.toLocalFile(),
                            'output' : self.format_output(n.toLocalFile()),
                            'status' : 'Waiting',
                            }
                          for n in names ]
        self.images_changed.emit()

    @pyqtSlot('QList<int>')
    def remove(self, indices):
        self._images = [ i for j, i in enumerate(self._images)
                         if j not in set(indices) ]
        self.images_changed.emit()

    @pyqtProperty('QVariant', notify=images_changed)
    def images(self):
        return self._images

    @pyqtProperty(float, notify=scale_chaged)
    def scale(self):
        return self._scale

    @pyqtSlot(float)
    def setScale(self, scale):
        if scale != self._scale:
            self._scale = scale
            self.scale_chaged.emit()

    @pyqtProperty(str, notify=output_format_changed)
    def outputFormat(self):
        return self.output_format

    @pyqtSlot(str)
    def setOutputFormat(self, fmt):
        self.output_format = fmt
        self.output_format_changed.emit()
        for img in self._images:
            img['output'] = self.format_output(img['name'])

    @pyqtProperty(bool, notify=tasks_finished)
    def running(self):
        return self.task_map == {}

    @pyqtSlot()
    def reset(self):
        for img in self._images:
            img['status'] = 'Waiting'
        self.images_changed.emit()

    @pyqtSlot()
    def clear(self):
        self._images = {}
        self.output_format = ''
        self.images_changed.emit()
        self.output_format_changed.emit()


def main(args=sys.argv, qml_code=None):
    app = QApplication(args)
    app.setApplicationName('Batch resizer')
    app.setOrganizationName('BSC')

    qmlEngine = QQmlApplicationEngine()
    imd = ImageMagickDispatcher()
    qmlEngine.rootContext().setContextProperty("imageMagickDispatcher", imd)

    if qml_code:
        qmlEngine.loadData(qml_code.encode())
    else:
        qmlEngine.load('resizer.qml')
    qmlEngine.quit.connect(app.quit)

    app.exec_()


QML_CODE=None


if __name__ == '__main__':
    main(qml_code=QML_CODE)
