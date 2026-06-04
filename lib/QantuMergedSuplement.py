from .QantuMergedProduct import QantuMergedProduct
from .QantuSuplement import QantuSuplement
import copy

class QantuMergedSuplement(QantuMergedProduct, QantuSuplement):
    def __init__(self, p1: QantuSuplement, p2: QantuSuplement):
        # init Suplement properties
        self.__dict__.update(copy.deepcopy(p1.__dict__))
        # initialize merged product properties
        QantuMergedProduct.__init__(self, p1, p2)
        
