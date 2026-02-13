import re
from datetime import datetime
import pandas
import math
from .QantuProduct import QantuProduct

class QantuGalenico(QantuProduct):
    def __init__(self, code, name, stock, disable, createdAt, minStock, price=0.0, cost=0.0):
        super().__init__(code, name, stock, disable, 'GALENICOS', createdAt, minStock, price, cost)
        listCaract=self.name.split()
        if self.validName(listCaract):
            if len(listCaract)==4:
                self.formula = listCaract[0]
                self.qtty = listCaract[1]
                self.presentation = listCaract[2]
                self.concentration = ""
            elif len(listCaract)==5:
                self.formula = listCaract[0]
                self.concentration = listCaract[1]
                self.qtty = listCaract[2]
                self.presentation = listCaract[3]
            else:
                print("WARN: Too much name params["+self.name+"]")
        else:
            print("WARN: Set to default void params ["+self.name+"]")
            self.concentration = ""
            self.ff = ""
            self.formula = ""
            self.qtty = ""
     
    def getConcentration(self):
        return self.concentration
    
    def getFormula(self):
        return self.formula
    
    def getQtty(self):
        return self.qtty
    
    def getPresentation(self):
        return self.presentation
    
    def validName(self, listCaract):
        if len(listCaract) > 5:
            print('ValidName: TOO LARGE NAME: '+ self.name)
            return False
        
        if len(listCaract) < 4:
            print('ValidName: TOO SHORT NAME: '+ self.name)
            return False
        
        return True

    def merge(self, prod):
        super().merge(prod)
        self.code = self.getFormula()+self.getConcentration()+self.getQtty()