import sys
sys.path.append('../')
from lib.QantuProduct import QantuProduct
from lib.QantuPackage import QantuPackage
from lib.ReportDownloader import ReportDownloader
from lib.QantuConfiguration import QantuConfiguration
from lib.SusiiProductLoader import SusiiProductLoader
import pandas
from datetime import datetime

colCosto = 'D'
colPrecio = 'E'
colVentas = 'F'
colMargen = 'H'

IGV=0.18

config = QantuConfiguration()
# business id
business_ = config.business_


def productSegment(summarySeg:dict[str,list], prod:QantuProduct, total, mcVal, mcrVal):
    seg1 = prod.getSeg1()
    seg2 = prod.getSeg2()
    seg3 = prod.getSeg3()
    if seg1 is not None and not pandas.isna(seg1) and len(seg1)>0:
        seg1U = seg1.upper()
        if seg1U in summarySeg:
            summarySeg[seg1U][0]=summarySeg[seg1U][0]+total
            summarySeg[seg1U][1]=summarySeg[seg1U][1]+mcVal
            summarySeg[seg1U][2]=summarySeg[seg1U][2]+mcrVal
        else:
            summarySeg[seg1U]=[total, mcVal, mcrVal]
    
    if seg2 is not None and not pandas.isna(seg2) and len(seg2)>0:
        seg2U = seg2.upper()
        if seg2U in summarySeg:
            summarySeg[seg2U][0]=summarySeg[seg2U][0]+total
            summarySeg[seg2U][1]=summarySeg[seg2U][1]+mcVal
            summarySeg[seg2U][2]=summarySeg[seg2U][2]+mcrVal
        else:
            summarySeg[seg2U]=[total, mcVal, mcrVal]
        
    if seg3 is not None and not pandas.isna(seg3) and len(seg3)>0:
        seg3U = seg3.upper()
        if seg3U in summarySeg:
            summarySeg[seg3U][0]=summarySeg[seg3U][0]+total
            summarySeg[seg3U][1]=summarySeg[seg3U][1]+mcVal
            summarySeg[seg3U][2]=summarySeg[seg3U][2]+mcrVal
        else:
            summarySeg[seg3U]=[total, mcVal, mcrVal]
        
    return summarySeg

def createDataList(packDict, prodDict):
    data = []
    summary:dict[str, list] = {}
    summarySeg:dict[str, list] = {}
    count = 0

    for key, prod in prodDict.items():
        count = count + 1
        mcu = '={colP}{rowP}-{colC}{rowC}'.format(colP=colPrecio, rowP=count+1,
                                                  colC=colCosto, rowC=count+1)
        mcup = '= {colM}{rowM}/{colP}{rowP}'.format(colM=colMargen, rowM=count+1,
                                                    colP=colPrecio, rowP=count+1)
        mc = '= {colM}{rowM}*{colV}{rowV}'.format(colM=colMargen, rowM=count+1,
                                                    colV=colVentas, rowV=count+1)
        total = prod.getPrice()*prod.getSoldUnits()
        l = [prod.getCode(), prod.getName(), prod.getCategory(),
                     prod.getLastCost(), prod.getPrice(), prod.getSoldUnits(),
                     total, mcu, mcup, mc]
        data.append(l)
        cat = prod.getCategory()
        mcVal = (prod.getPrice()-prod.getLastCost())*prod.getSoldUnits()
        mcrVal = mcVal/(1+IGV)
        if cat in summary:
            summary[cat][0]=summary[cat][0]+total
            summary[cat][1]=summary[cat][1]+mcVal
            summary[cat][2]=summary[cat][2]+mcrVal
        else:
            summary[cat]=[total, mcVal, mcrVal]
        
        summarySeg = productSegment(summarySeg, prod, total, mcVal, mcrVal)
        
    for key, pack in packDict.items():
        count = count + 1
        mcu = '={colP}{rowP}-{colC}{rowC}'.format(colP=colPrecio, rowP=count+1,
                                                  colC=colCosto, rowC=count+1)
        mcup = '= {colM}{rowM}/{colP}{rowP}'.format(colM=colMargen, rowM=count+1,
                                                    colP=colPrecio, rowP=count+1)
        mc = '= {colM}{rowM}*{colV}{rowV}'.format(colM=colMargen, rowM=count+1,
                                                    colV=colVentas, rowV=count+1)
        total = pack.getPrice()*pack.getSoldUnits()
        l = [pack.getCode(), pack.getName(), pack.getCategory(), 
                     pack.getCost(), pack.getPrice(), pack.getSoldUnits(),
                     total, mcu, mcup, mc]
        data.append(l)
        cat = pack.getCategory()
        mcVal = (pack.getPrice()-pack.getCost())*pack.getSoldUnits()
        mcrVal = mcVal/(1+IGV)
        if cat in summary:
            summary[cat][0]=summary[cat][0]+total
            summary[cat][1]=summary[cat][1]+mcVal
            summary[cat][2]=summary[cat][2]+mcrVal
        else:
            summary[cat]=[total, mcVal, mcrVal]
        
        for code, prod in pack.itemsObj.items():
            total = prod.getPrice()*pack.items[code]*pack.getSoldUnits()
            mcVal = (prod.getPrice()-prod.getLastCost())*pack.items[code]*pack.getSoldUnits()
            mcrVal = mcVal/(1+IGV)
            summarySeg = productSegment(summarySeg, prod, total, mcVal, mcrVal)
    
    summaryData=[]
    for key in summary:
        summaryData.append([key, summary[key][0], summary[key][1], summary[key][2]])
    
    largeName:dict[str,str]={
    'DIG' : 'Salud Digestiva',
    'AUX' : 'Primeros Auxilios',
    'RES' : 'Salud Respiratoria',
    'DEP' : 'Promocion del Deporte',
    'HTA' : 'Cuidado del Hipertenso',
    'TRB' : 'Salud del Trabajador',
    'ORT' : 'Salud Ortopedica',
    'KID' : 'Salud del niño',
    'STR' : 'Control del estrés',
    'BEBE' : 'Cuidado del bebé',
    'FACE' : 'Cuido del rostro',
    'CAB' : 'Cuidado del Cabello',
    'PIEL' : 'Cuidado de la piel',
    'ADM' : 'Cuidado del adulto mayor',
    'PER' : 'Aseo Personal',
    'BUC' : 'Salud bucal',
    'REP' : 'Salud Reproductiva'}
    summarySegData=[]
    for key in summarySeg:
        if key in largeName:
            summarySegData.append([key, largeName[key],summarySeg[key][0], summarySeg[key][1], summarySeg[key][2]])
        else:
            summarySegData.append([key, "",summarySeg[key][0], summarySeg[key][1], summarySeg[key][2]])
    
    return data, summaryData, summarySegData

def run():
    # Enter period
    year = input("Enter year YYYY: ")
    month = input("Enter month mm: ")
    beginDt = year+"-"+month+"-01"
    #lastDay = calendar.monthrange(int(year), int(month))[1]
    monthNum=int(month)
    endMonthNum = monthNum+1
    if endMonthNum == 13:
        endMonthNum=1
        yearNum = int(year)+1
        year = str(yearNum)
    endMonth = "{:02d}".format(endMonthNum)
    endDt = year+"-"+endMonth+"-01"

    now = datetime.now().strftime("%Y-%m-%d")

    # download sales per product
    loader = SusiiProductLoader(business_)
    loader.setBeginDateSaleData(beginDt)
    loader.setEndDateSaleData(endDt)

    # load products from q1
    prodDict:dict[str, QantuProduct] = loader.downloadProducts(downloadSaleData=True)
    if not prodDict:
        print("Fail to downloadProducts.")
        sys.exit(2)

    # load products from q1
    packDict:dict[str, QantuPackage] = loader.downloadPackages(downloadSaleData=True)
    if not packDict:
        print("Fail to downloadPackages.")
        sys.exit(3)

    
    #download expenses
    repHeaders = ["DESCRIPCIÓN", "CATEGORÍA", "MONTO"]
    rd = ReportDownloader("Exportar gastos.xlsx", "export_payments_expenses",
                          repHeaders, beginDt, endDt)
    file_expenses = rd.execute()
    if file_expenses == '':
        sys.exit("Can't dowloand file[Exportar gastos.xlsx]")

    exp_df = pandas.read_excel(file_expenses, skiprows=4)
    print("REG SIZE (expenses):"+str(len(exp_df)))

    sum_row = exp_df[['MONTO']].sum()
    sum_row['DESCRIPCIÓN'] = 'Total'
    sum_row['CATEGORÍA'] = 'Todas'
    sum_df = pandas.DataFrame([sum_row], columns=exp_df.columns)
    exp_df = pandas.concat([exp_df, sum_df], ignore_index=True)

    data, summaryData, summarySegData = createDataList(packDict, prodDict)
    #count = len(data)

    cols = ['COD', 'NOMBRE', 'CATEGORIA', 'COSTO', 'PRECIO', 'VENTAS',
            'TOTAL', 'Mcu', 'Mcu%', 'Mc']
    out_df = pandas.DataFrame(data, columns = cols)

    colsSummary = ['CAT', 'VOL VENTAS', 'MC', 'MCR']
    out2_df = pandas.DataFrame(summaryData, columns = colsSummary)
    sum_row = out2_df[['VOL VENTAS', 'MC', 'MCR']].sum()
    sum_row['CAT'] = 'Total'
    sum_df = pandas.DataFrame([sum_row], columns=out2_df.columns)
    out2_df = pandas.concat([out2_df, sum_df], ignore_index=True)
    
    colsSummarySeg = ['CODE', 'CAT', 'VOL VENTAS', 'MC', 'MCR']
    out3_df = pandas.DataFrame(summarySegData, columns = colsSummarySeg)
    sum_row = out3_df[['VOL VENTAS', 'MC', 'MCR']].sum()
    sum_row['CAT'] = 'Total'
    sum_df = pandas.DataFrame([sum_row], columns=out3_df.columns)
    out3_df = pandas.concat([out3_df, sum_df], ignore_index=True)

    now = datetime.now().strftime("%Y%m%d")
    excel_name = str(business_)+'_Utilidad_'+year+month+'_'+now+'.xlsx'

    with pandas.ExcelWriter(excel_name) as excel_writer:
        out_df.to_excel(excel_writer, sheet_name='Utilidad', index=False)
        out2_df.to_excel(excel_writer, sheet_name='Summary', index=False)
        out3_df.to_excel(excel_writer, sheet_name='Segments', index=False)
        exp_df.to_excel(excel_writer, sheet_name='Expenses', index=False)


run()