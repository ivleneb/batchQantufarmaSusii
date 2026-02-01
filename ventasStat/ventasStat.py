import sys
sys.path.append(r'../')
import pandas
from datetime import datetime
#from lib.libclass import *
from lib.ReportDownloader import ReportDownloader
import json

# Read JSON file
with open('../lib/cfg.json', 'r', encoding='utf-8') as file:
    dataCfg = json.load(file)
    business_ = dataCfg["businessId"]

class HourStat:
    def __init__(self, hour):
        self.hour = hour
        self.amt = 0.0
        self.tick = 0
        
    def addSale(self, amt):
        self.amt += amt
        self.tick += 1
        
    def getAmt(self):
        return self.amt
    
    def getTickets(self):
        return self.tick
    
    def getAmtPerTicket(self):
        if self.tick != 0:
            return self.amt/self.tick
        else:
            return 0.0

class DiaStat:
    def __init__(self, dia):
        self.dia = dia
        self.amt = 0.0
        self.tick = 0
        
    def addSale(self, amt):
        self.amt += amt
        self.tick += 1
        
    def getAmt(self):
        return self.amt
    
    def getTickets(self):
        return self.tick
    
    def getAmtPerTicket(self):
        if self.tick != 0:
            return self.amt/self.tick
        else:
            return 0.0

class SellerStat:
    def __init__(self, seller):
        self.seller = seller
        self.dictHour = {f"{i:02d}": HourStat(f"{i:02d}") for i in range(7, 23)}
        
    def addSale(self, amt, hour):
        if not hour in self.dictHour:
            self.dictHour[hour]=HourStat(hour)
        self.dictHour[hour].addSale(amt)


def getHora(date):
    ls = date.split()
    hh = ls[1][0:2]
    return hh

def getDia(date):
    ls = date.split()
    fecha_str = ls[0]
    fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
    numero_dia = fecha.weekday()
    # Convertir a texto
    dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    nombre_dia = dias_semana[numero_dia]
    return nombre_dia

def summaryStats(salesDataFile, days):
    # dataframe Products
    sales_df = pandas.read_excel(salesDataFile, skiprows=8)

    dictSeller = {}
    dictHour = {f"{i:02d}": HourStat(f"{i:02d}") for i in range(7, 23)}
    dictDia = {}
    
    # For each pack
    for index, row in sales_df.iterrows():
        hh = getHora(row['FECHA'])
        dia = getDia(row['FECHA'])
        seller = row['VENDEDOR']
        amt = row['IMPORTE TOTAL DEL COMPROBANTE']
        
        if not seller in dictSeller:
            dictSeller[seller]=SellerStat(seller)
        dictSeller[seller].addSale(amt, hh)
         
        if not hh in dictHour:
            dictHour[hh]=HourStat(hh)
        dictHour[hh].addSale(amt)
        
        if not dia in dictDia:
            dictDia[dia]=DiaStat(dia)
        dictDia[dia].addSale(amt) 
            
    print("Summary")
    
    # 
    data1 = {}
    for seller, data in dictSeller.items():
        print("Vendedor: "+seller)
        for hour, hourData in data.dictHour.items():
            if not seller in data1:
                data1[seller] = []
            amt = hourData.getAmt()
            ticks = hourData.getTickets()
            amtPerTick = hourData.getAmtPerTicket()
            data1[seller].append([hour, amt, ticks, amtPerTick, amt/days, ticks/days, amtPerTick/days])
            print("Hora:"+hour+" Monto:"+str(hourData.getAmt())+" Tickets:"+str(hourData.getTickets()))
    
    print("GENERAL")
    data2 = []
    for hour, hourData in dictHour.items():
        amt = hourData.getAmt()
        ticks = hourData.getTickets()
        amtPerTick = hourData.getAmtPerTicket()
        data2.append([hour, amt, ticks, amtPerTick, amt/days, ticks/days, amtPerTick/days])
        print("Hora:"+hour+" Monto:"+str(hourData.getAmt())+" Tickets:"+str(hourData.getTickets()))
    
    cols = ['HORA', 'MONTO TOT', 'TICKETS TOT', 'MONTOxTICK', 'MONTOXDIA', 'TICKETXDIA', 'PROMEDIOXDIA']
    out_df = pandas.DataFrame(data2, columns = cols)
    
    print("DIAS")
    data3 = []
    for dia, diaData in dictDia.items():
        amt = diaData.getAmt()
        ticks = diaData.getTickets()
        amtPerTick = diaData.getAmtPerTicket()
        data3.append([dia, amt, ticks, amtPerTick, amt/days, ticks/days, amtPerTick/days])
        print("Dia:"+dia+" Monto:"+str(diaData.getAmt())+" Tickets:"+str(diaData.getTickets()))
    
    cols = ['DIA', 'MONTO TOT', 'TICKETS TOT', 'MONTOxTICK', 'MONTOXDIA', 'TICKETXDIA', 'PROMEDIOXDIA']
    dia_df = pandas.DataFrame(data3, columns = cols)
    
    now = datetime.now().strftime("%Y%m%d")
    excel_name = str(business_)+'_StatVentasPorHora_'+now+'.xlsx'

    with pandas.ExcelWriter(excel_name) as excel_writer:
        out_df.to_excel(excel_writer, sheet_name='General', index=False)
        dia_df.to_excel(excel_writer, sheet_name='Dias', index=False)
        for seller in data1:
            seller_df = pandas.DataFrame(data1[seller], columns = cols)
            seller_df.to_excel(excel_writer, sheet_name=seller, index=False)
        

def diferencia_dias(fecha1, fecha2):
    try:
        fecha1 = datetime.strptime(fecha1, '%Y-%m-%d')
        fecha2 = datetime.strptime(fecha2, '%Y-%m-%d')
        return abs((fecha2 - fecha1).days)
    except ValueError as e:
        print(f"Error en formato de fecha: {e}")
        return None

def run():
    # Enter period
    beginDt = input("Enter start date YYYY-MM-DD: ")
    endDt = input("Enter end date YYYY-MM-DD: ")

    days = diferencia_dias(endDt, beginDt)
    if days==None:
        exit(1)
    print("Days: "+str(days))

    repHeaders = ["FECHA", "IMPORTE TOTAL DEL COMPROBANTE", "VENDEDOR"]

    rd = ReportDownloader("Exportar ventas.xlsx", "export_sales",
                          repHeaders, beginDt, endDt)
    file1 = rd.execute()


    if file1=='':
        print("Faltan archivos")
    else:
        print("Download ok")
        summaryStats(file1, days)

run()