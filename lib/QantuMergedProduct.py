import re
from datetime import datetime
import pandas
import math
from .QantuProduct import QantuProduct

class QantuMergedProduct:
    def getCode(self):
        return self.code
    
    def getName(self):
        return self.mergedName
    
    def setName(self, name):
        self.mergedName=name
    
    def getLastCost(self):
        return self.mergedLastCost
    
    def setLastCost(self, cost):
        self.mergedLastCost = cost
    
    def getLastProvider(self):
        return self.mergedLastProvider
    
    def setLastProvider(self, provider):
        self.mergedLastProvider = provider
    
    def getStock(self):
        return self.mergedStock
    
    def setStock(self, stock):
        self.mergedStock = stock
    
    def getSoldUnits(self):
        return self.mergedSoldUnits
    
    def setSoldUnits(self, units):
        self.mergedSoldUnits = units
        
    def getCreatedAt(self):
        return self.mergedCreatedAt
    
    def setCreatedAt(self, created):
        self.mergedCreatedAt = created
        
    def getActiveDays(self):
        return self.mergedActiveDays
    
    def setActiveDays(self, days):
        self.mergedActiveDays = days
    
    def __init__(self, p1: QantuProduct, p2: QantuProduct):        
        self.mergedName = ""
        self.mergedLastCost = 0
        self.mergedLastProvider = ""
        self.mergedStock = 0
        self.mergedSoldUnits = 0
        self.mergedCreatedAt = None
        self.mergedActiveDays = 1
        
        # append name according to sale mean
        if p2.getLastCost() < p1.getLastCost():
            self.setName(p2.getUnitsCajaName() +'\n ó '+ p1.getUnitsCajaName())
            self.setLastCost(p2.getLastCost())
            self.setLastProvider(p2.getLastProvider())
        else:
            self.setName(p1.getUnitsCajaName()+'\n ó '+p2.getUnitsCajaName())
            self.setLastCost(p1.getLastCost())
            self.setLastProvider(p1.getLastProvider())
        
        # update stocks and sold units
        self.setStock(p1.getStock()+p2.getStock())
        self.setSoldUnits(p1.getSoldUnits()+p2.getSoldUnits())
        
        # update active days
        if p1.getActiveDays() < p2.getActiveDays():
            self.setCreatedAt(p2.getCreatedAt())
            self.setActiveDays(p2.getActiveDays())
        else:
            self.setCreatedAt(p1.getCreatedAt())
            self.setActiveDays(p1.getActiveDays())
        
        #if self.minStock < prod.getMinStock():
        #    self.setMinStock(prod.getMinStock())
        
        # last provider is NaN
        if p2.getLastProvider() != p2.getLastProvider() and p1.getLastProvider() == p1.getLastProvider():
            print("PROD "+p2.getName()+" last provides is NULL")
            self.setLastProvider(p1.getLastProvider())
        elif p2.getLastProvider() == p2.getLastProvider() and p1.getLastProvider() != p1.getLastProvider():
            self.setLastProvider(p2.getLastProvider())
        elif p1.getLastProvider() is None or (len(p1.getLastProvider()) < 2 and len(p2.getLastProvider())>=2):
            self.setLastProvider(p2.getLastProvider())
        else:
            self.setLastProvider(p1.getLastProvider())
            
        
        self.products = { p1.getCode(): p1, p2.getCode(): p2}
        self.code = "MERGED"+p1.getCode()
    
    def merge(self, prod:QantuProduct):
        self.products[prod.getCode]=prod
        if prod.getLastCost() < self.getLastCost():
            self.setName(prod.getUnitsCajaName() +'\n ó '+ self.getName())
            self.setLastCost(prod.getLastCost())
            self.setLastProvider(prod.getLastProvider())
        else:
            self.setName(self.getName()+'\n ó '+prod.getUnitsCajaName())
        
        # update stocks and sold units
        self.setStock(self.getStock()+prod.getStock())
        self.setSoldUnits(self.getSoldUnits()+prod.getSoldUnits())
        
        # update active days
        if self.getActiveDays() < prod.getActiveDays():
            self.setCreatedAt(prod.getCreatedAt())
            self.setActiveDays(prod.getActiveDays())

        # last provider is NaN
        if prod.getLastProvider() != prod.getLastProvider():
            print("PROD "+prod.getName()+" last provider is NaN")
        elif self.getLastProvider() != self.getLastProvider():
            self.setLastProvider(prod.getLastProvider())
        elif self.getLastProvider() is None or (len(self.getLastProvider()) < 2 and len(prod.getLastProvider())>=2):
            self.setLastProvider(prod.getLastProvider())
        
    def combine(self, prod):
        self.products.update(prod.products)
        if prod.getLastCost() < self.getLastCost():
            self.setName(prod.getName() +'\n ó '+ self.getName())
            self.setLastCost(prod.getLastCost())
            self.setLastProvider(prod.getLastProvider())
        else:
            self.setName(self.getName()+'\n ó '+prod.getName())
        
        # update stocks and sold units
        self.setStock(self.getStock()+prod.getStock())
        self.setSoldUnits(self.getSoldUnits()+prod.getSoldUnits())
        
        # update active days
        if self.getActiveDays() < prod.getActiveDays():
            self.setCreatedAt(prod.getCreatedAt())
            self.setActiveDays(prod.getActiveDays())

        # last provider is NaN
        if prod.getLastProvider() != prod.getLastProvider():
            print("PROD "+prod.getName()+" last provider is NaN")
        elif self.getLastProvider() != self.getLastProvider():
            self.setLastProvider(prod.getLastProvider())
        elif self.getLastProvider() is None or (len(self.getLastProvider()) < 2 and len(prod.getLastProvider())>=2):
            self.setLastProvider(prod.getLastProvider())
