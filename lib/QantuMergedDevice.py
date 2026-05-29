from .QantuMergedProduct import QantuMergedProduct
from .QantuDevice import QantuDevice
import copy

class QantuMergedDevice(QantuMergedProduct, QantuDevice):
    def __init__(self, p1: QantuDevice, p2: QantuDevice):
        # init device properties
        self.__dict__.update(copy.deepcopy(p1.__dict__))
        # initialize merged product properties
        QantuMergedProduct.__init__(self, p1, p2)
        