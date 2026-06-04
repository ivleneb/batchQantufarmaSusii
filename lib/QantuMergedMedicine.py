from .QantuMergedProduct import QantuMergedProduct
from .QantuMedicine import QantuMedicine
import copy

class QantuMergedMedicine(QantuMergedProduct, QantuMedicine):
    def __init__(self, p1: QantuMedicine, p2: QantuMedicine):
        # init device properties
        self.__dict__.update(copy.deepcopy(p1.__dict__))
        # initialize merged product properties
        QantuMergedProduct.__init__(self, p1, p2)
        if self.isGenerico():
            self.code = self.getFormula()+self.getConcentration()+self.getFFSimple()+str(self.getCantidad())+'GEN'
        else:
            self.code = self.getPrincipioActivo()+self.getConcentration()+self.getFFSimple()+str(self.getCantidad())+'MAR'
        
