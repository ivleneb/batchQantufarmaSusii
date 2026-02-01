import re
from datetime import datetime
import pandas
import math
from .QantuProduct import QantuProduct

class QantuDevice(QantuProduct):
    def __init__(self, code, name, stock, disable, createdAt, minStock, price=0.0, cost=0.0):
        super().__init__(code, name, stock, disable, 'DISPOSITIVOS MEDICOS', createdAt, minStock, price, cost)
        listCaract=self.name.split()
        if self.validName(listCaract):
            self.type = listCaract[0]
            self.characteristic = listCaract[1]
            self.qtty = listCaract[2]
        else:
            print("WARN: Set to default void params ["+self.name+"]")
            self.type = ""
            self.characteristic = ""
            self.qtty = ""
     
    def getType(self):
        return self.type
    
    def getCharacteristic(self):
        return self.characteristic
    
    def getQtty(self):
        return self.qtty

    def validName(self, listCaract):
        if len(listCaract)!=4:
            print('ValidName: WRONG LENGTH: '+ self.name)
            return False
        
        return True
