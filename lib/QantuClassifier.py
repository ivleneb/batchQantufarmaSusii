from .QantuProduct import QantuProduct
from .PropertyLoader import PropertyLoader

class QantuClassifier:
    
    @staticmethod
    def digemidRegCode(prod: QantuProduct):
        regSan = prod.getNumRegSan()
        regSan = regSan.strip()
        if ('-' in regSan and len(regSan)>10) or len(regSan)>9:
            return None
        
        lsCodes = PropertyLoader.getRegDigCodes()
        
        xyz = regSan[0:3]
        if xyz in lsCodes:
            return xyz
        
        xy = regSan[0:2]
        if xy in lsCodes:
            return xy
        
        return None
    
    @staticmethod
    def digesaRegCode(prod: QantuProduct):
        regSan = prod.getNumRegSan()
        regSan = regSan.strip()
        if len(regSan)!=9:
            return None
        elif not regSan[8] in ('N', 'E'):
            return None
        elif any(c.isalpha() for c in regSan[1:8]):
            return None 
        
        lsCodes = PropertyLoader.getRegDigesaCodes()
        
        xyz = regSan[0:3]
        if xyz in lsCodes:
            return xyz
        
        return None