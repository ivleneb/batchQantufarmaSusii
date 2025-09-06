import sys
sys.path.append('../')
import pandas
from datetime import datetime
from lib.libclass import *
from lib.RequestHandler import *
from lib.WharehouseMovement import *


# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    user_ = data["user"]
    pass_ = data["password"]
    uri_ = data["uri"]
    business_ = data["businessId"]
     
lsMove=[]

def retrieveMoveList(beginDtl, endDtl, page=1):
    uri = "/v1/warehouses/warehouse-movements/?number=&content_type__model=adjustment&page="+str(page)+"&business="+str(business_)+"&date__gte="+beginDtl+"T05:00:00.000Z&date__lte="+endDtl+"T04:59:59.999Z"
    print(uri)
    rd = RequestHandler(uri)
    res = rd.execute()

    if res != None:
        for move in res['results']:
            print(move['number'])
            lsMove.append(move['id'])
    
    pageSize = res['page_size']
    
    if page>10:
        print("Too many requests!")
        return 1
    elif len(res['results'])>pageSize:
        page+=1
        return retrieveMoveList(beginDtl, endDtl, page)
    else:
        print(len(res['results']))
        return 0

def formatDate(dt):
    # Convertir a objeto datetime
    fecha_obj = datetime.fromisoformat(dt)
    # Formatear como deseas
    dateF = fecha_obj.strftime('%Y-%m-%d %H:%M')
    
    return dateF

def getInfoAdjust(ls, pcode):
    motive = ''
    cost = ''
    qtt = ''
    nro = ''
    for i in range(len(ls)):
        if pcode in ls[i]:
            try:
                motiveStr = ls[i+1].replace(" ", "")
                if 'MOTIVO' in motiveStr:
                    motiveLs = motiveStr.split(':')
                    motive = motiveLs[1]
                else:
                    print("[WARNING] Literal 'MOTIVO' not present in "+motiveStr+"\n")
                    return '','','',''
                qttStr = ls[i+2].replace(" ", "")
                if 'CANTIDAD' in qttStr:
                    qttLs = qttStr.split(':')
                    qtt = qttLs[1]
                else:
                    print("[WARNING] Literal 'CANTIDAD' not present in "+qttStr+"\n")
                    return '','','',''
                costStr = ls[i+3].replace(" ", "")
                if 'MONTO' in costStr:
                    costLs = costStr.split(':')
                    cost = costLs[1]
                else:
                    print("[WARNING] Literal 'MONTO' not present in "+costStr+"\n")
                    return '','','',''
                nroStr = ls[i+4].replace(" ", "")
                if 'NRO' in nroStr:
                    nroLs = nroStr.split(':')
                    nro = nroLs[1]
                else:
                    print("[WARNING] Literal 'MONTO' not present in "+costStr+"\n")
                    return '','','','' 
                return motive, cost, qtt, nro
            except IndexError as e:
                print(f"[WARNING] Error: {e}")
            finally:
                return motive, cost, qtt, nro
                
    print("[WARNING] Product code "+pcode+" not found!")
    return '','','',''

def processInactiveMove(move):
    date = formatDate(move.getDate())
    username = move.getUser()['username']
    number = move.getNumber()
    direction = move.getDirection()
    obs = move.getObs()
    
    ls = []
    ls.append([date, username, number, direction, obs])
    return ls

def processInternalUse(move):
    date = formatDate(move.getDate())
    username = move.getUser()['username']
    number = move.getNumber()
    direction = move.getDirection()

    ls = []
    for rec in move.getRecords():
        ls.append([date, username, number, direction, rec['product']['code'], rec['product']['name'], rec['quantity']])
        
    return ls

def processTransfer(move):
    date = formatDate(move.getDate())
    username = move.getUser()['username']
    number = move.getNumber()
    direction = move.getDirection()

    ls = []
    for rec in move.getRecords():
        ls.append([date, username, number, direction, rec['product']['code'], rec['product']['name'], rec['quantity']])
        
    return ls

def processAdjust(move, prevMove):
    date = formatDate(move.getDate())
    username = move.getUser()['username']
    number = move.getNumber()
    direction = move.getDirection()
    obs = move.getObs()
    
    obs = obs.upper()
    obsLsDir = obs.split('\n')
    obsLs = [ elem for elem in obsLsDir if elem != '' ]
    
    ls = []
    
    if len(obsLs)!=4 and len(obsLs)!=5:
        comm = "[WARNING] AJUSTE "+str(number)+": OBSERVACION NO CUMPLE EL FORMATO:"+obs+"\n"
        print(comm)
        ls.append([date, username, number, direction, obs, comm])
        return False, ls
    
    for rec in move.getRecords():
        motive, cost, quant, nro = getInfoAdjust(obsLs, rec['product']['code'])
        
        if '' in [motive, cost, quant]:
            print([motive, cost, quant])
            comm = "[WARNING] AJUSTE "+str(number)+": getInfoAdjust for "+str(rec['product']['code'])+" retornó valores inválidos."
            print(comm)
            lsVoid = []
            lsVoid.append([date, username, number, direction, obs, comm])
            return False, lsVoid
        
        if float(quant) != float(rec['quantity']):
            comm = "[WARNING] AJUSTE "+str(number)+": CANTIDAD DE PRODUCTO "+str(rec['product']['code'])+" NO COINCIDE CON OBS. ("+quant+"!="+rec['quantity']+")"
            print(comm)
            lsVoid = []
            lsVoid.append([date, username, number, direction, obs, comm])
            return False, lsVoid
        
        costF = float(cost)
        costF = round(costF, 2)
        msg = ''
        if costF > 0.0 and direction=='Salida':
            msg = 'Revisar signo'
        elif costF < 0.0 and direction=='Entrada':
            msg = 'Revisar signo'
        
        ls.append([date, username, number, direction, rec['product']['code'], rec['product']['name'], rec['quantity'], motive, costF, msg])

    return True, ls

def processExpired(move):
    date = formatDate(move.getDate())
    username = move.getUser()['username']
    number = move.getNumber()
    direction = move.getDirection()
    
    ls = []
    for rec in move.getRecords():
        costBuy = 0.0
        sellPrice = rec['product']['selling_price']
        buyPrice = rec['product']['last_buy_price']
        if buyPrice != None:
            costBuy = float(rec['quantity'])*float(buyPrice)
        costSale = 0.0
        if sellPrice != None:
            costSale = float(rec['quantity'])*float(sellPrice)
        ls.append([date, username, number, direction, rec['product']['code'], rec['product']['name'], rec['quantity'], -costSale, -costBuy])
        
    return ls
        
def processOther(move):
    date = formatDate(move.getDate())
    username = move.getUser()['username']
    number = move.getNumber()
    direction = move.getDirection()
    obs = move.getObs()
    
    ls = []
    ls.append([date, username, number, direction, obs])
    return ls
        
headInactiveMove = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'OBS']
inactiveMoveDat = []
headOtherMove = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'OBS']
otherMoveDat = []
headUsoInterno = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'COD PROD', 'NOMBRE PROD', 'CANTIDAD']
usoInternoDat = []
headTraslado = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'COD PROD', 'NOMBRE PROD', 'CANTIDAD']
trasladoDat = []
headInvalidAdjust = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'OBS', 'MOT RECHAZO']
invalidAdjustDat = []
headValidAdjust = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'COD PROD', 'NOMBRE PROD', 'CANTIDAD', 'MOTIVO', 'COSTO', 'COMENTARIOS']
validAdjustDat = []
headExpired = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'COD PROD', 'NOMBRE PROD', 'CANTIDAD', 'COSTO VENTA', 'COSTO COMPRA']
expiredDat = []

def process(move, prevMove, usoInterno, traslado, validAdjust, invalidAdjust, expired, inactiveMove, otherMove):
    user = move.getUser()
    state = move.getState()
    obs = move.getObs()
    number = move.getNumber()
    if state:
        #typ = WharehouseMovementClassifier(move).getType() #moveType(obs)
        #move.setType(typ)
        typ = move.getMoveType()
        if typ == 'INTERNAL_USE':
            usoInterno += processInternalUse(move)
        elif typ == 'TRANSFER':
            traslado += processTransfer(move)
        elif typ == 'ADJUST':
            isValid, mat = processAdjust(move)
            if isValid:
                validAdjust += mat
            else:
                invalidAdjust += mat
        elif typ == 'EXPIRED':
            expired += processExpired(move)
        else:
            print("Other type of movement:"+str(number)+" by "+user['username'])
            print(obs)
            print("\n\n")
            otherMove += processOther(move)
    else:
        inactiveMove += processInactiveMove(move)

# Enter period
year = input("Enter year YYYY: ")
month = input("Enter month mm: ")
beginDt = year+"-"+month+"-01"

monthNum=int(month)
endMonthNum = monthNum+1
if endMonthNum == 13:
    endMonthNum=1
    yearNum=int(year)
    year=str(yearNum+1)
endMonth = "{:02d}".format(endMonthNum)
endDt = year+"-"+endMonth+"-01"

if retrieveMoveList(beginDt, endDt) == 0:
    print("List retrieved ok")
    unique_list = list(set(lsMove))
    
    prevMovim = None
    for idMove in unique_list:
        uri="/warehouses/warehouse-movements/"+str(idMove)+"/?business="+str(business_)
        print(uri)
        rd = RequestHandler(uri)
        res = rd.execute()
        
        if res != None:
            movim = WharehouseMovement(res)
            process(movim, prevMovim, usoInternoDat, trasladoDat, validAdjustDat, invalidAdjustDat, expiredDat, inactiveMoveDat, otherMoveDat)
            prevMovim = WharehouseMovement(res)
        else:
            print("No response!")

else:
    print("List retrieve fail")
    
    
# create data drames
usoInterno_df = pandas.DataFrame(usoInternoDat, columns = headUsoInterno)
traslado_df = pandas.DataFrame(trasladoDat, columns = headTraslado)
validAdjust_df = pandas.DataFrame(validAdjustDat, columns = headValidAdjust)
invalidAdjust_df = pandas.DataFrame(invalidAdjustDat, columns = headInvalidAdjust)
expired_df = pandas.DataFrame(expiredDat, columns = headExpired)
inactiveMove_df = pandas.DataFrame(inactiveMoveDat, columns = headInactiveMove)
otherMove_df = pandas.DataFrame(otherMoveDat, columns = headOtherMove)

now = datetime.now().strftime("%Y%m%d_%H%M")
excel_name = str(business_)+'_ReporteAlmacen_'+now+'.xlsx'
with pandas.ExcelWriter(excel_name) as excel_writer:
    usoInterno_df.to_excel(excel_writer, sheet_name='Uso Interno', index=False)
    traslado_df.to_excel(excel_writer, sheet_name='Traslados', index=False)
    validAdjust_df.to_excel(excel_writer, sheet_name='Ajustes', index=False)
    invalidAdjust_df.to_excel(excel_writer, sheet_name='Ajustes Invalidos', index=False)
    expired_df.to_excel(excel_writer, sheet_name='Vencidos', index=False)
    inactiveMove_df.to_excel(excel_writer, sheet_name='Mov Deshabilitados', index=False)
    otherMove_df.to_excel(excel_writer, sheet_name='Mov No identificados', index=False)
    
        
print("------------------------  END ---------------------------")
