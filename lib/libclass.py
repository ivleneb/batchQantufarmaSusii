import re
from datetime import datetime
import pandas
import math

class QantuProduct:
    def __init__(self, code, name, stock=None, disable=None,
                 category=None, createdAt=None, minStock=None,
                 price=None, cost=None, commPer=0.10, otc='Y'):
        self.name = re.sub(' +', ' ', name)
        self.category = category
        self.code = code
        self.disable = disable
        self.stock = stock
        self.lastCost = cost
        self.price = price
        self.commissionPer = commPer
        self.commission = self.commissionPer*(self.price-self.lastCost)
        self.soldUnits = 0
        self.lastProvider = None
        if createdAt==None or type(createdAt)==float or len(createdAt)==0:
            print("WARNING: Not valid CREATED AT for "+self.name)
            self.createdAt = '2023/05/27'
        else:
            self.createdAt = createdAt
        today = datetime.now()
        try:
            delta = today - datetime.strptime(self.createdAt, "%Y/%m/%d")
        except ValueError:
            print("ERROR: invalid createdAt format "+self.name)
            exit(1)
        self.activeDays = delta.days
        
        if minStock != minStock:
            self.minStock = 0
        else:
            self.minStock = minStock
        
        self.otc = otc
    
    def merge(self, prod):
        self.addStock(prod.getStock())
        self.addSoldUnits(prod.getSoldUnits())
        if self.activeDays < prod.getActiveDays():
            self.setCreatedAt(prod.getCreatedAt())
            self.setActiveDays(prod.getActiveDays())
        
        if self.minStock < prod.getMinStock():
            self.setMinStock(prod.getMinStock())
    
    def getCreatedAt(self):
        return self.createdAt
    
    def setCreatedAt(self, createdAt):
        self.createdAt = createdAt
    
    def getMinStock(self):
        return self.minStock
    
    def setMinStock(self, stock):
        self.minStock = stock
    
    def getActiveDays(self):
        return self.activeDays
    
    def setActiveDays(self, days):
        self.activeDays = days
    
    def getLastProvider(self):
        return self.lastProvider
    
    def setLastProvider(self, provider):
        self.lastProvider = provider
    
    def getStock(self):
        return self.stock
    
    def addStock(self, stock):
        self.stock = self.stock + stock
    
    def getLastCost(self):
        return self.lastCost
    
    def setLastCost(self, cost):
        self.lastCost = cost
    
    def getPrice(self):
        return self.price
    
    def setPrice(self, price):
        self.price = price
    
    def getName(self):
        return self.name

    def getCategory(self):
        return self.category
    
    def getCode(self):
        return self.code
    
    def getSoldUnits(self):
        return self.soldUnits
    
    def setSoldUnits(self, sold):
        self.soldUnits = sold
    
    def addSoldUnits(self, sold):
        self.soldUnits = self.soldUnits + sold
    
    def isDisable(self):
        return self.disable==1

    def isNoUsar(self):
        return self.name.find('NO USAR')!=-1
    
    def getCommission(self):
        return self.commission
    
    def getBrand(self):
        return self.brand
    
    def setBrand(self, brand):
        self.brand = brand
    
    def getOtc(self):
        return self.otc
        
    def setOtc(self, otc):
        self.otc = otc
    
    def getFechaVto(self):
        return self.fechaVto
    
    def setFechaVto(self, fechaVto):
        self.fechaVto = fechaVto.replace(" ", "").upper()
        if "S" in self.fechaVto and "V" in self.fechaVto:
            self.remainingDays = 1000
            return
        
        today = datetime.now()
        try:
            delta = None
            if self.fechaVto.count("/")==2:
                delta = datetime.strptime(self.fechaVto, "%Y/%m/%d") - today
            else:
                delta = datetime.strptime(self.fechaVto+"/01", "%Y/%m/%d") - today
            self.remainingDays = delta.days
        except ValueError:
            if self.stock != 0:
                print("ERROR: invalid fechaVto format "+self.fechaVto+" "+self.name)
            self.remainingDays = 0
    
    def getRemainingDays(self):
        return self.remainingDays
    
class QantuSuplement(QantuProduct):
    def __init__(self, code, name, price, cost):
        super().__init__(code=code, name=name, category='SUPLEMENTOS',
                         price=price, cost=cost, commPer=0.1)

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

class QantuPackage():
    def __init__(self, code, name, price=0.0, cost=0.0, category=None):
        self.code = code
        self.name = name
        self.items={}
        self.soldUnits = None
        self.cost = cost
        self.price = price
        self.category = category
        self.generico = None
        self.commissionPer=0.04
        self.commission = self.commissionPer*(self.price-self.cost)
    
    def getName(self):
        return self.name

    def addItem(self, prodCode, quantity:int):
        self.items[prodCode]=quantity
    
    def getSoldUnits(self):
        return self.soldUnits
    
    def setSoldUnits(self, sold):
        self.soldUnits = sold
        
    def getCode(self):
        return self.code
    
    def getItems(self):
        return self.items
    
    def getCost(self):
        return self.cost
    
    def setCost(self, cost):
        self.cost = cost
        self.commission = self.commissionPer*(self.price-self.cost)

    def getPrice(self):
        return self.price
    
    def setPrice(self, price):
        self.price = price
        
    def getCategory(self):
        return self.category
    
    def setCategory(self, category):
        self.category = category
        
    def setGenerico(self, generico):
        self.generico = generico
        
    def isGenerico(self):
        return self.generico
    
    def getCommission(self):
        return self.commission
        
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
        
    def getCommission(self):
        return self.commission
    
    def printSummary(self):
        self.data['producto'].append("TOTAL")
        self.data['comisión'].append("")
        self.data['cantidad'].append("")
        self.data['sub-total'].append(self.commission)
        df = pandas.DataFrame(self.data)
        #df.loc['Total'] = df.sum(numeric_only=True)
        df.to_excel(self.name+'.xlsx', index=False)