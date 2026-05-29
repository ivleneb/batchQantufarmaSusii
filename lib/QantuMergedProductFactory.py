from .QantuMergedProduct import QantuMergedProduct
from .QantuMergedDevice import QantuMergedDevice
from .QantuDevice import QantuDevice

class QantuMergedProductFactory:
    @staticmethod
    def merge(prod1, prod2):
        if isinstance(prod1, QantuMergedProduct) and not isinstance(prod2, QantuMergedProduct):
            print("CASE 1")
            prod1.merge(prod2)
            return prod1
        elif not isinstance(prod1, QantuMergedProduct) and isinstance(prod2, QantuMergedProduct):
            print("CASE 2")
            prod2.merge(prod1)
            return prod2
        elif isinstance(prod1, QantuMergedProduct) and isinstance(prod2, QantuMergedProduct):
            print("CASE 3")
            prod1.combine(prod2)
            return prod1
        else:
            print("CASE 4")
            if isinstance(prod1, QantuDevice):
                return QantuMergedDevice(prod1, prod2)
            else:
                Exception("Type "+prod1.getCategory()+" Not implemented yet")