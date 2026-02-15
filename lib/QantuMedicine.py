import re
from datetime import datetime
import pandas
import math
from .QantuProduct import QantuProduct

class QantuMedicine(QantuProduct):
    def __init__(self, code, name, stock=None, disable=None,
                 createdAt=None, minStock=None, price=0.0, cost=0.0, generico=0):
        super().__init__(code, name, stock, disable, 'MEDICAMENTOS', createdAt, minStock, price, cost)
        self.generico = generico
        self.setMedProperties()
        
    def setMedProperties(self):
        listCaract=self.name.split()
        if self.validName(listCaract):
            self.concentration = listCaract[1]
            try:
                self.cantidad = int(listCaract[3])
            except ValueError:
                print("VALUE ERROR: "+self.name)
                self.cantidad = 0
                
            self.ff = listCaract[4]
            self.formula = listCaract[0]
            ls = re.split(r'[()]', self.formula)
            # for non -generic meds
            if len(ls)>1:
                self.principioActivo = ls[1]
            else:
                self.principioActivo = ""
        else:
            self.concentration = ""
            self.ff = ""
            self.formula = ""
            self.principioActivo = ""
            self.cantidad = 0
        
    def validName(self, listCaract):
        if len(listCaract) < 5:
            print('ValidName: TOO SHORT NAME: '+ self.name)
            return False
        
        if listCaract[2] == 'X':
            return True
        elif listCaract[2] == 'x':
            print('ValidName: AMBIGUOUS NAME: '+ self.name)
            return True
        else:
            print('ValidName: NO X OR BAD POS: '+ self.name)
            return False
    
    def getConcentration(self):
        return self.concentration
    
    def getFormula(self):
        return self.formula
    
    def getFF(self):
        return self.ff
    
    def isGenerico(self):
        return self.generico==1
    
    def valBrand(self):
        return self.generico
    
    def setGenerico(self, gen):
        self.generico = gen
    
    def setUnitsCaja(self, unitsCaja):
        if math.isnan(unitsCaja):
            self.unitsCaja = 0
        else:
            self.unitsCaja = unitsCaja
    
    def getUnitsCaja(self):
        return self.unitsCaja
    
    def setUnitsBlister(self, unitsBlister):
        self.unitsBlister = unitsBlister
    
    def getUnitsBlister(self):
        return self.unitsBlister
    
    def getPrincipioActivo(self):
        return self.principioActivo
    
    def getCantidad(self):
        return self.cantidad
    
    def merge(self, prod):
        super().merge(prod)
        if self.isGenerico():
            self.code = self.getFormula()+self.getConcentration()+self.getFF()+str(self.getCantidad())+'GEN'
        else:
            self.code = self.getPrincipioActivo()+self.getConcentration()+self.getFF()+str(self.getCantidad())+'MAR'
            
    def getFFSimple(self):
        return self.ff.removesuffix("_REC")        
