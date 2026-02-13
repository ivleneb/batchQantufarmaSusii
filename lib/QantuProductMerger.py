import sys
sys.path.append(r'../')
from lib.QantuMedicine import QantuMedicine
from lib.QantuGalenico import QantuGalenico
from lib.QantuDevice import QantuDevice
from lib.QantuGeneral import QantuGeneral
from lib.QantuPackage import QantuPackage
from lib.QantuProduct import QantuProduct
#from lib.PriceManager import PriceManager
from lib.ReportDownloader import ReportDownloader
import pandas
from datetime import datetime
import json


class QantuProductMerger:
    @staticmethod
    def combineProducts(prodDict):
        prodDict=QantuProductMerger.combineMedicines(prodDict)
        prodDict=QantuProductMerger.combineGalenicos(prodDict)
        prodDict=QantuProductMerger.combineMedDevices(prodDict)
        
        return prodDict
    
    @staticmethod
    def combineMedicines(prodDict):
        # Combine medicine items with same form and concentration
        print("Second product filter")
        for code in list(prodDict):
            if not code in prodDict:
                continue
            prod = prodDict[code]
            if prod.getCategory() != 'MEDICAMENTOS':
                continue
            
            formu = prod.getFormula()
            if formu == "":
                print("WARNING: Invalid formula for MED "+prod.getName())
                continue
            cc = prod.getConcentration()
            if cc == "":
                print("WARNING: Invalid CC for MED "+prod.getName())
                continue
            ff  = prod.getFF()
            if ff == "":
                print("WARNING: Invalid FF for MED "+prod.getName())
                continue
            qq = prod.getCantidad()
            if qq == 0:
                print("WARNING: Invalid QQ for MED"+prod.getName())
                continue
            if prod.valBrand()==2:
                print("GOLD PRODUCT: "+prod.getName())
                continue
            
            if prod.isGenerico():
                for code2 in list(prodDict):
                    if code == code2:
                        continue
                    if not code in prodDict:
                        continue
                    prod2 = prodDict[code2]
                    if prod2.getCategory() != 'MEDICAMENTOS':
                        continue
                    
                    if formu == prod2.getFormula():
                        if cc == prod2.getConcentration():
                            if ff == prod2.getFF():
                                if qq == prod2.getCantidad():
                                    print("MERGING:"+prod.getName()+" AND "+prod2.getName())
                                    prod.merge(prod2)
                                    del prodDict[code2]
            else:
                #print("NOT GENERIC:"+prod.getName())
                for code2 in list(prodDict):
                    if code == code2:
                        continue
                    if not code in prodDict:
                        continue
                    prod2 = prodDict[code2]
                    if prod2.getCategory() != 'MEDICAMENTOS':
                        continue
                    if prod2.valBrand()==2:
                        continue
                    
                    if prod.getPrincipioActivo()!="" and (prod.getPrincipioActivo() == prod2.getPrincipioActivo()):
                        if cc == prod2.getConcentration():
                            if ff == prod2.getFF():
                                if qq == prod2.getCantidad():
                                    print("MERGING:"+prod.getName()+" AND "+prod2.getName())
                                    prod.merge(prod2)
                                    del prodDict[code2]
        return prodDict

    # Combine galenics items with same form and concentration
    @staticmethod
    def combineGalenicos(prodDict):
        print("Third product filter")
        for code in list(prodDict):
            if not code in prodDict:
                continue
            prod = prodDict[code]
            if prod.getCategory() != 'GALENICOS':
                continue
            #print("Get formula")
            formu = prod.getFormula()
            if formu == "":
                print("WARNING: Invalid formula["+prod.getName()+"]")
                continue
            ##print("Get CC")
            cc = prod.getConcentration()

            ##print("Get Qtty")
            qtty = prod.getQtty()
            if qtty == "":
                print("WARNING: Invalid qtty["+prod.getName()+"]")
                continue

            for code2 in list(prodDict):
                if code == code2:
                    continue
                if not code in prodDict:
                    continue
                prod2 = prodDict[code2]
                if prod2.getCategory() != 'GALENICOS':
                    continue
                
                if formu == prod2.getFormula():
                    if cc == prod2.getConcentration():
                        if qtty == prod2.getQtty():
                            prod.merge(prod2)
                            del prodDict[code2]
        return prodDict

    # Combine med devs items with same type, mark, subcategory, qtty and units
    @staticmethod
    def combineMedDevices(prodDict):
        print("Fourth product filter")
        for code in list(prodDict):
            if not code in prodDict:
                continue
            prod = prodDict[code]
            if prod.getCategory()!='DISPOSITIVOS MEDICOS':
                continue
            typ = prod.getType()
            if typ == "":
                print("WARNING: Invalid device type["+prod.getName()+"]")
                continue
            ch = prod.getCharacteristic()
            if ch == "":
                print("WARNING: Invalid device characteristic["+prod.getName()+"]")
                continue
            qtty = prod.getQtty()
            if qtty == "":
                print("WARNING: Invalid device qtty["+prod.getName()+"]")
                continue

            for code2 in list(prodDict):
                if code == code2:
                    continue
                if not code in prodDict:
                    continue
                prod2 = prodDict[code2]
                if prod2.getCategory()!='DISPOSITIVOS MEDICOS':
                    continue
                if typ == prod2.getType():
                    if ch == prod2.getCharacteristic():
                        if qtty == prod2.getQtty():
                            prod.merge(prod2)
                            del prodDict[code2]
        return prodDict

    # Combine med devs items with same type, mark, subcategory, qtty and units
    @staticmethod
    def combineAseo(prodDict):
        print("Five product filter")
        for code in list(prodDict):
            if not code in prodDict:
                continue
            prod = prodDict[code]
            if prod.getCategory() not in ['ASEO', 'BELLEZA', 'BEBES']:
                continue
            #print("ASEO1:"+prod.getName())
            typ = prod.getType()
            #print(typ)
            if typ == "":
                print("WARNING: Invalid general type["+prod.getName()+"]")
                continue
            brand = prod.getBrand()
            #print(brand)
            if brand == "":
                print("WARNING: Invalid general brand["+prod.getName()+"]")
                continue
            ch = prod.getCharacteristic()
            #print(ch)
            if ch == "":
                print("WARNING: Invalid general characteristic["+prod.getName()+"]")
                continue
            cnt = prod.getContent()
            #print(cnt)
            if cnt == "":
                print("WARNING: Invalid general content["+prod.getName()+"]")
                continue

            for code2 in list(prodDict):
                if code == code2:
                    continue
                if not code in prodDict:
                    continue
                prod2 = prodDict[code2]
                if prod2.getCategory() not in ['ASEO', 'BELLEZA', 'BEBES']:
                    continue

                if typ == prod2.getType():
                    if brand == prod2.getBrand():
                        if cnt == prod2.getContent():
                            #print("Match!")
                            prod.merge(prod2)
                            del prodDict[code2]
        return prodDict

