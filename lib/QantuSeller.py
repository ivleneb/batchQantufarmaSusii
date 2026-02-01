import re
from datetime import datetime
import pandas
import math
from .QantuProduct import QantuProduct
from .QantuPackage import QantuPackage

class QantuSeller():
    def __init__(self, name):
        self.name = name
        self.commission = 0
        self.data = {'producto':[], 'comisión':[], 'cantidad':[], 'sub-total':[]} 
        
    def addCommission(self, prod:QantuProduct, cant):
        comm = prod.getCommission()*cant
        self.commission = self.commission + comm
        self.data['producto'].append(prod.getName())
        self.data['comisión'].append(prod.getCommission())
        self.data['cantidad'].append(cant)
        self.data['sub-total'].append(comm)
        
    def addPkgCommission(self, pack:QantuPackage, cant):
        comm = pack.getCommission()*cant
        self.commission = self.commission + comm
        self.data['producto'].append(pack.getName())
        self.data['comisión'].append(pack.getCommission())
        self.data['cantidad'].append(cant)
        self.data['sub-total'].append(comm)
        
    def getCommission(self, r2:int=2):
        if r2!=0:
            return round(self.commission, r2)
        else:
            return self.commission
    
    def printSummary(self):
        self.data['producto'].append("TOTAL")
        self.data['comisión'].append("")
        self.data['cantidad'].append("")
        self.data['sub-total'].append(self.commission)
        df = pandas.DataFrame(self.data)
        #df.loc['Total'] = df.sum(numeric_only=True)
        df.to_excel(self.name+'.xlsx', index=False)