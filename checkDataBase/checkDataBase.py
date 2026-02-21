import sys
sys.path.append(r'../')
from lib.QantuProduct import QantuProduct
from lib.QantuConfiguration import QantuConfiguration
from datetime import datetime
from lib.SusiiProductLoader import SusiiProductLoader
import pandas
import numpy as np

# load configuration
config = QantuConfiguration()
# business id
business_ = config.business_

def generateReportFile(errorList):
    
    cols2 = ["CÓDIGO", "NOMBRE", "COL", "VALOR", "ERROR"
            ]


    report_df = pandas.DataFrame(errorList, columns = cols2)
    now = datetime.now().strftime("%Y%m%d")
    excel_name = str(business_)+'_Errores_'+now+'.xlsx'
    with pandas.ExcelWriter(excel_name) as excel_writer:
        report_df.to_excel(excel_writer, index=False)

def isVoid(value):
    if pandas.isna(value) or value is None or (type(value)==str and len(value)==0):
        return True
    else:
        return False

def invalidValue(value, ls):
    if value in ls:
        return False
    else:
        return True
        
def invalidInt(value):
    if type(value)==int or isinstance(value, np.integer):
        return False
    else:
        return True

def isNumeric(value):
    if isinstance(value, (int, float, complex)) or isinstance(value, (np.integer, np.floating, np.complexfloating)):
        return True
    else:
        return False

def validDate(dt):
    dt = dt.replace(" ", "").upper()
        
    if "S" in dt and "V" in dt:
        return True
    
    try:
        if dt.count("/")==2:
            date = datetime.strptime(dt, "%Y/%m/%d")
        else:
            date= datetime.strptime(dt+"/01", "%Y/%m/%d")
            
        return True
    except ValueError:
        return False

def run():
    loader = SusiiProductLoader(business_)

    # load products from q1
    productDict:dict[str, QantuProduct] = loader.downloadProducts()
    if not productDict:
        print("Fail to downloadProducts.")
        sys.exit(2)
    
    errorList = []
    # for p1 in products of q1
    for prodCode in productDict:
        # copy values from main (q1) to other store
        prod = productDict[prodCode]
        
        if prod.getStock()<=0 or prod.getCategory()=='OFICINA':
            continue
        
        name = prod.getName()
        
        cat = prod.getCategory()
        if isVoid(cat):
            errorList.append([prodCode, name, "CATEGORY", "Valor vacío", cat])
        
        lab = prod.getBrand()
        if isVoid(cat):
            errorList.append([prodCode, name, "LAB", "Valor vacío", lab])
        
        pLogic = prod.getPriceLogic()
        if isVoid(pLogic):
            errorList.append([prodCode, name, "PRICE LOGIC", "Valor vacío", pLogic])
        validVals = [0,1]
        if invalidValue(pLogic, validVals):
            errorList.append([prodCode, name, "PRICE LOGIC", 
            "Valor inválido ["+",".join(map(str,validVals))+"]", pLogic])
        
        if prod.getCategory()=='MEDICAMENTOS':
            
            tt = prod.getTipoTratamiento()
            if isVoid(tt):
                errorList.append([prodCode, name, "TIPO TRATAMIENTO", "Valor vacío", tt])
            validVals = [0,1]
            if invalidValue(tt, validVals):
                errorList.append([prodCode, name, "TIPO TRATAMIENTO", 
                "Valor inválido ["+",".join(map(str,validVals))+"]", tt])
            
            otc = prod.getOtc()
            #if isVoid(otc):
            #    errorList.append([prodCode, name, "OTC", "Valor vacío", otc])
            validVals = ['Y', 'N']
            if not isVoid(otc) and invalidValue(otc, validVals):
                errorList.append([prodCode, name, "OTC", 
                "Valor inválido ["+",".join(validVals)+"]", otc])
            
            gen = prod.getGenerico()
            #if isVoid(gen):
            #    errorList.append([prodCode, name, "GENERICO", "Valor vacío", gen])
            validVals = [0,1,2]
            if not isVoid(gen) and invalidValue(gen, validVals):
                errorList.append([prodCode, name, "GENERICO", 
                "Valor inválido ["+",".join(map(str,validVals))+"]", gen])
            
            # validations for specific forms
            if not ('TAB' in prod.getFF()) and not ('CAP' in prod.getFF()):
                continue
            
            uBli = prod.getUnitsBlister()
            if isVoid(uBli):
                errorList.append([prodCode, name, "UNITS BLISTER", "Valor vacío", uBli])
            if not isNumeric(uBli):
                errorList.append([prodCode, name, "UNITS BLISTER", 
                "Valor inválido [entero]", uBli])
        
        uCaj = prod.getUnitsCaja()
        if isVoid(uCaj):
            errorList.append([prodCode, name, "UNITS CAJA", "Valor vacío", uCaj])
        if not isNumeric(uCaj):
            errorList.append([prodCode, name, "UNITS CAJA", 
            "Valor inválido [entero]", uCaj])
        
        #prod.getSeg1()
        #prod.getSeg2()
        #prod.getSeg3()
            
        vto = prod.getFechaVto()
        if isVoid(vto):
            errorList.append([prodCode, name, "FECHA VTO", "Valor vacío", vto])
        if not validDate(vto):
            errorList.append([prodCode, name, "FECHA VTO", 
            "Valor inválido", vto])
        
        lote = prod.getNroLote()
        if isVoid(lote):
            errorList.append([prodCode, name, "NRO LOTE", "Valor vacío", lote])

        regSan = prod.getNumRegSan()
        if isVoid(regSan):
            errorList.append([prodCode, name, "NUM REG SAN", "Valor vacío", regSan])
        
        creat = prod.getCreatedAt()
        if isVoid(creat):
            errorList.append([prodCode, name, "CREATED AT", "Valor vacío", creat])
        if not validDate(creat):
            errorList.append([prodCode, name, "CREATED AT", 
            "Valor inválido", creat])
    
    generateReportFile(errorList)

run()