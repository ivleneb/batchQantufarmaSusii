import re
from datetime import datetime
import pandas
import math

class QantuPackage():
    def __init__(self, code, name, price=0.0, cost=0.0, category=None, alias=None, unidad=None):
        self.code = code
        self.name = name
        self.items={}
        self.itemsObj={}
        self.soldUnits = None
        self.cost = cost
        self.price = price
        self.category = category
        self.generico = None
        self.commissionPer=0.04
        self.commission = self.commissionPer*(self.price-self.cost)
        self.alias = alias
        self.unidad = unidad
    
    def getName(self):
        return self.name

    def addItem(self, prodCode, quantity:int):
        self.items[prodCode]=quantity
        
    def addItemObj(self, prodObj):
        self.itemsObj[prodObj.getCode()] = prodObj
    
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
    
    def getAlias(self):
        return self.alias
    
    def setAlias(self, alias):
        self.alias = alias
        
    def getUnidad(self):
        return self.unidad
    
    def setUnidad(self, unidad):
        self.unidad = unidad
