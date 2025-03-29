import sys, os
sys.path.append(r'F:\proyectos\botica\qantufarma')
import pandas
from datetime import datetime
from lib.libclass import *
from lib.FileDownloader import *

    
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

rd = FileDownloader(beginDt, endDt)
ok = rd.execute()


if not ok:
    print("Faltan archivos")
else:
    print("Download ok")
