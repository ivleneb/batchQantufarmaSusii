import sys, os
sys.path.append(r'../')
import pandas
from datetime import datetime
from lib.libclass import *
from lib.ReportDownloader import *

# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    business_ = data["businessId"]

def getTime(date):
    arr = date.split() # date is in 'dd/MM/YYYY HH:mm' format
    hhmmStr = arr[1]
    hhmmInt = int(hhmmStr.replace(":", ""))
    return hhmmInt

def toMinutes(hhmm):
    mm = hhmm%100;
    hh = int(hhmm/100)
    return hh*60+mm

userRemain = {}
enterTable = 1000
if business_ == 8132:
    enterTable = 700
tolerance = 15
def summaryRemainingTime(cashMovementDataFile):
    # dataframe Products
    cashmove_df = pandas.read_excel(cashMovementDataFile, skiprows=4)
    
    # For each pack
    for index, row in cashmove_df.iterrows():
        if "inicio" in row["DESCRIPCIÓN"].lower():
            # if morning turn
            timeInt = getTime(row["FECHA"])
            if timeInt<1300:
                diff = toMinutes(timeInt)-toMinutes(enterTable)
                if diff >= 0:
                    if diff > tolerance:
                        remain = diff-tolerance
                        if not (row["USUARIO"] in userRemain):
                            userRemain[row["USUARIO"]]=0
                        userRemain[row["USUARIO"]]+=remain
                        print(row)
                        print(row["USUARIO"]+" add to remain "+str(remain))
                else:
                    if not (row["USUARIO"] in userRemain):
                        userRemain[row["USUARIO"]]=0
                    userRemain[row["USUARIO"]]+=diff
                    print(row)
                    print(row["USUARIO"]+" recupero "+str(abs(diff))+" min")
                
    print("Summary")
    for user, timeRemain in userRemain.items():
        print(user+" remaining time in minutes:"+str(timeRemain))
            

# Enter period
year = input("Enter year YYYY: ")
month = input("Enter month mm: ")
beginDt = year+"-"+month+"-01"
#beginDt2 = '2023-05-27'
monthNum=int(month)
endMonthNum = monthNum+1
if endMonthNum == 13:
    endMonthNum=1
    yearNum=int(year)
    year=str(yearNum+1)
endMonth = "{:02d}".format(endMonthNum)
endDt = year+"-"+endMonth+"-01"

repHeaders = ["DESCRIPCIÓN", "TIPO", "FECHA", "USUARIO"]

rd = ReportDownloader("Exportar movimientos de caja chica.xlsx", "export_petty_cash_movements",
                      repHeaders, beginDt, endDt)
file1 = rd.execute()


if file1=='':
    print("Faltan archivos")
else:
    print("Download ok")
    summaryRemainingTime(file1)
