import sys
sys.path.append(r'../')
from lib.QantuProduct import QantuProduct
from lib.QantuConfiguration import QantuConfiguration
from datetime import datetime
from lib.SusiiProductLoader import SusiiProductLoader
import pandas
import numpy as np
from lib.BatchUtils import BatchUtils
from lib.PropertyLoader import PropertyLoader
from lib.QantuClassifier import QantuClassifier
from typing import Union, List

# load configuration
config = QantuConfiguration()
# business id
business_ = config.business_

def generateReportFile(errorList):
    
    cols2 = ["CÓDIGO", "NOMBRE", "COL", "ERROR", "VALOR"
            ]


    report_df = pandas.DataFrame(errorList, columns = cols2)
    now = datetime.now().strftime("%Y%m%d")
    excel_name = str(business_)+'_Errores_'+now+'.xlsx'
    out_path = './out'
    BatchUtils.crear_carpeta_si_no_existe(out_path)
    fullpath = out_path+'/'+excel_name
    with pandas.ExcelWriter(fullpath) as excel_writer:
        report_df.to_excel(excel_writer, index=False)

def isVoid(value):
    if pandas.isna(value) or value is None or (type(value)==str and len(value)==0):
        return True
    else:
        return False

def invalidValue(value, ls:Union[List[int], List[str]]):
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
            datetime.strptime(dt, "%Y/%m/%d")
        else:
            datetime.strptime(dt+"/01", "%Y/%m/%d")
            
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
        
        
        numProps = len(name.split())
        if cat=='MEDICAMENTOS' and numProps!=6:
            errorList.append([prodCode, name, "NAME", "Longitud de caracteristicas invalida MEDICAMENTOS, debe ser 6", ''])
        elif cat=='GALENICOS' and not numProps in [4,5]:
            errorList.append([prodCode, name, "NAME", "Longitud de caracteristicas invalida GALENICOS, debe ser 4 o 5", ''])
        elif cat=='DISPOSITIVOS MEDICOS' and numProps != 4:
            errorList.append([prodCode, name, "NAME", "Longitud de caracteristicas invalida DISPOSITIVOS, debe ser 4", ''])
        elif not cat in ('MEDICAMENTOS','GALENICOS','DISPOSITIVOS MEDICOS') and numProps != 4:
            errorList.append([prodCode, name, "NAME", "Longitud de caracteristicas invalida GENERAL, debe ser 4", ''])
        
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
        
        if cat=='MEDICAMENTOS':
            
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
            validVals2 = ['Y', 'N']
            if not isVoid(otc) and invalidValue(otc, validVals2):
                errorList.append([prodCode, name, "OTC", 
                "Valor inválido ["+",".join(validVals2)+"]", otc])
            
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
        else:
            code = QantuClassifier.digemidRegCode(prod)
            if code is None:
                if cat in ('MEDICAMENTOS', 'GALENICOS', 'SUPLEMENTOS'):
                    errorList.append([prodCode, name, "NUM REG SAN", "El codigo del registro sanitario es invalido", regSan])
                continue
            
            listCodePerCat = PropertyLoader.getRegCodePerCategory()
            
            if code in listCodePerCat['GALENICOS'] and prod.getCategory()!='GALENICOS':
                errorList.append([prodCode, name, "NUM REG SAN", "Categorizar como GALENICOS", regSan+" code:"+code])
            elif code in listCodePerCat['MEDICAMENTOS'] and prod.getCategory()!='MEDICAMENTOS':
                errorList.append([prodCode, name, "NUM REG SAN", "Categorizar como MEDICAMENTOS", regSan+" code:"+code])
            elif code in listCodePerCat['SUPLEMENTOS'] and prod.getCategory()!='SUPLEMENTOS':
                errorList.append([prodCode, name, "NUM REG SAN", "Categorizar como SUPLEMENTOS", regSan+" code:"+code])
            elif code in listCodePerCat['PRODMEDNOCAT'] and not isVoid(prod.getCategory()):
                errorList.append([prodCode, name, "NUM REG SAN", "NO HAY UNA CATEGORIA DEFINIDA, REPORTAR!!", regSan+" code:"+code])
            elif prod.getCategory()=='MEDICAMENTOS' and not (code in listCodePerCat['MEDICAMENTOS']):
                errorList.append([prodCode, name, "NUM REG SAN", "Registro sanitario no corresponde a MEDICAMENTOS", regSan+" code:"+code])
            elif prod.getCategory()=='GALENICOS' and not (code in listCodePerCat['GALENICOS']):
                errorList.append([prodCode, name, "NUM REG SAN", "Registro sanitario no corresponde a GALENICOS", regSan+" code:"+code])
            elif prod.getCategory()=='SUPLEMENTOS' and  not (code in listCodePerCat['SUPLEMENTOS']):
                errorList.append([prodCode, name, "NUM REG SAN", "Registro sanitario no corresponde a SUPLEMENTOS", regSan+" code:"+code])
                
        creat = prod.getCreatedAt()
        if isVoid(creat):
            errorList.append([prodCode, name, "CREATED AT", "Valor vacío", creat])
        if not validDate(creat):
            errorList.append([prodCode, name, "CREATED AT", 
            "Valor inválido", creat])        
        
        seg1 = prod.getSeg1()
        if isVoid(seg1):
            errorList.append([prodCode, name, "SEG 1", "Valor vacío", seg1])
        
        segCodes:dict[str,str]=PropertyLoader.getSegCodes()
        seg2 = prod.getSeg2()
        seg3 = prod.getSeg3()
        if not isVoid(seg2) and (not seg1 in segCodes.keys()):
            errorList.append([prodCode, name, "SEG 1", "Valor inválido", seg1])
        if not isVoid(seg2) and (not seg2 in segCodes.keys()):
            errorList.append([prodCode, name, "SEG 2", "Valor inválido", seg2])
        if not isVoid(seg3) and (not seg3 in segCodes.keys()):
            errorList.append([prodCode, name, "SEG 3", "Valor inválido", seg3])
        
        price = prod.getPrice()
        cost = prod.getLastCost()
        mcp = (price-cost)/price
        mcpper = round(mcp*100,2)
        ideal = round(cost/0.9, 2)
        if mcpper < 10 and prod.getPriceLogic():
            errorList.append([prodCode, name, "PRICE", "MC% es menor al 10%. Minimum price "+str(ideal), mcpper])
        
    generateReportFile(errorList)

run()