from .QantuMergedProduct import QantuMergedProduct
from .QantuGalenico import QantuGalenico
import copy

class QantuMergedGalenico(QantuMergedProduct, QantuGalenico):
    def __init__(self, p1: QantuGalenico, p2: QantuGalenico):
        # init Galenico properties
        self.__dict__.update(copy.deepcopy(p1.__dict__))
        # initialize merged product properties
        QantuMergedProduct.__init__(self, p1, p2)
        self.code = self.getFormula()+self.getConcentration()+self.getQtty()        
