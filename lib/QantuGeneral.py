import re
from datetime import datetime
import pandas
import math
from .QantuProduct import QantuProduct

class QantuGeneral(QantuProduct):
    def __init__(self, code, name, stock=None, disable=None, category=None, createdAt=None,
                 minStock=None, price=0.0, cost=0.0):
        super().__init__(code, name, stock, disable, category, createdAt, minStock, price, cost)
        listCaract=self.name.split()
        if self.validName(listCaract):
            self.type = listCaract[0]
            self.brand = listCaract[1]
            self.characteristic = listCaract[2]
            self.content = listCaract[3]
        else:
            print("WARN: Set to default void params ["+self.name+"]")
            self.type = ""
            self.brand = ""
            self.characteristic = ""
            self.qtty = ""
     
    def getType(self):
        return self.type
    
    def getBrand(self):
        return self.brand
    
    def getCharacteristic(self):
        return self.characteristic
    
    def getContent(self):
        return self.content

    def validName(self, listCaract):
        if len(listCaract)!=4:
            print('ValidName: WRONG LENGTH: '+ self.name)
            return False
        
        return True
