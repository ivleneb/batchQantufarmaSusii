import sys
sys.path.append('../')
from reports.WarehouseMovementReport import WarehouseMovementReport
from lib.RequestHandler import RequestHandler
import json

from lib.QantuConfiguration import QantuConfiguration

config = QantuConfiguration()
# credentials
business_ = config.business_
user_ = config.user_
pass_ = config.pass_
uri_ = config.uri_
     
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

wmp = WarehouseMovementReport(business_, year, month)

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
            wmp.process_movement(res)
        else:
            print("No response!")

else:
    print("List retrieve fail")

wmp.generate_summary()
wmp.export_report()
        
print("------------------------  END ---------------------------")