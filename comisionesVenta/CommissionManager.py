import sys #, os
sys.path.append('../')
import pandas
#from datetime import datetime
from lib.QantuProduct import QantuProduct
from lib.QantuSeller import QantuSeller
from lib.QantuSuplement import QantuSuplement
from lib.QantuGeneral import QantuGeneral
from lib.QantuPackage import QantuPackage
from lib.RequestHandler import RequestHandler

from lib.ReportDownloader import ReportDownloader

class CommissionManager:
    
    def __init__(self, businessId=None):
        self.categoriesEnabled={'QANTUFARMA.RUTH (USUARIO)':['SUPLEMENTOS', 'MEDICAMENTOS'],
                       'QANTUFARMA.JENNY (USUARIO)':['SUPLEMENTOS', 'MEDICAMENTOS'],
                       'QANTUFARMA.MIRIAM (USUARIO)':['SUPLEMENTOS', 'MEDICAMENTOS'],
                       'QANTUFARMA.ROSANGELA2 (USUARIO)':['SUPLEMENTOS', 'MEDICAMENTOS']
                       }
        
        self.prodDBDict = {}
        self.businessId = businessId
        
    def getCommissionPer(self, amount):
        rang:dict[int, float] = {8000	: 0.03,
                                8500	: 0.04,
                                9000	: 0.05,
                                9500	: 0.06,
                                10000	: 0.07,
                                10500	: 0.08,
                                11000	: 0.09,
                                11500	: 0.10,
                                12000	: 0.11
                }
        ls = list(rang.keys())
        commission = 0.0
        for index in range(len(ls)-1):
            if amount<ls[0]:
                break
            elif amount>=ls[index] and amount<ls[index+1]:
                key = ls[index]
                commission = rang[key]
                break
            elif amount>=ls[len(ls)-1]:
                commission = rang[len(ls)-1]
                break
        return commission

    def getProductDB(self, row):
        return QantuProduct(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'],
                                row['disable (EXTRA)'], row['CATEGORÍA'], row['creado (EXTRA)'], row['STOCK MÍNIMO'],
                                 row['PRECIO DE VENTA'], row['PRECIO DE COMPRA'])

    def addSaleData(self, prod, sale_df):
        sub_df = sale_df.loc[sale_df['CÓDIGO'] == prod.getCode()]
        if len(sub_df)==1:
            row = sub_df.iloc[0]
            # add sale data
            #prod.setLastProvider(row['ÚLTIMO PROVEEDOR'])
            prod.setSoldUnits(row['CANTIDAD TOTAL'])
        elif len(sub_df)==0:
            print("Product ["+prod.getName()+"] never sale!")
            prod.setSoldUnits(0)
        else:
            raise Exception("Code with multiple products.")

    def getSellers(self, df):
        column_names = list(df.columns.values)
        sellersLs = []
        for col in column_names:
            if "(USUARIO)" in col:
                sellersLs.append(col)
        sellerDict = {}
        for elem in sellersLs:
            sellerDict[elem]=QantuSeller(elem)
        return sellerDict

    def saleData(self, sale_df, code):
        sub_df = sale_df.loc[sale_df['CÓDIGO'] == code]
        if len(sub_df)>=1:
            return True, sub_df.iloc[0]
        else:
            return False, None  
            

    def getProduct(self, row):
        if row["CATEGORÍA"]=='SUPLEMENTOS':
            return QantuSuplement(row['CÓDIGO'], row['NOMBRE'],
                                  row['PRECIO DE VENTA'], row['PRECIO DE COMPRA'])
        else:
            return QantuProduct(code=row['CÓDIGO'], name=row['NOMBRE'], category=row['CATEGORÍA'],
                                price=row['PRECIO DE VENTA'], cost=row['PRECIO DE COMPRA'], commPer=self.commission)


    def getPackage(self, pack_df, code):
        sub_df = pack_df.loc[pack_df['CÓDIGO'] == code]
        if len(sub_df)>0:
            row = sub_df.iloc[0]
            pack = QantuPackage(row['CÓDIGO'], row['NOMBRE'], row['PRECIO DE VENTA'], category=row['CATEGORÍA'])
            cost = 0
            pName = pack.getName()
            for index, row in sub_df.iterrows():
                #print(f"Adding {row['NOMBRE (ITEM)']} X {row['CANTIDAD (ITEM)']} to {row['NOMBRE']}")
                cantItem = row['CANTIDAD (ITEM)']
                codeItem = row['CÓDIGO (ITEM)']
                pack.addItem(codeItem, cantItem)
                if codeItem in self.prodDBDict:
                    prod = self.prodDBDict[codeItem]
                    cost=cost+cantItem*prod.getLastCost()
                else:
                    print(f"Index[{index}] Package {code}[{pName}] item not found {codeItem}")
                
            pack.setCost(cost)
            return pack
        else:
            return None


    def summaryCommission(self, ProductsDataFile, salesDataFile, PackDataFile):
        # dataframe Products
        products_df = pandas.read_excel(ProductsDataFile, skiprows=4)
        # dataframe sales
        sales_df = pandas.read_excel(salesDataFile, skiprows=5)
        # dataframe pack
        pack_df = pandas.read_excel(PackDataFile, skiprows=4)
        
        # Load products DB
        for index, row in products_df.iterrows():
            prod = self.getProductDB(row)
            if prod != None and not prod.isDisable() and not prod.isNoUsar():
                self.addSaleData(prod, sales_df)
                if prod.getCode() in self.prodDBDict:
                    raise Exception("Index["+str(index)+"] Key must be unique")
                self.prodDBDict[prod.getCode()]=prod

        # initiaize sellers dictionary
        seller_dc = self.getSellers(sales_df)
        #print(seller_dc)
        
        # For each product
        for index, row in products_df.iterrows():
            # if product sold is Product
            hasSale, sale = self.saleData(sales_df, row['CÓDIGO'])
            if hasSale:
                prod = self.getProduct(row)
                if prod is not None:
                    # add net commission each user
                    for name, seller in seller_dc.items():
                        if prod.getCategory() not in self.categoriesEnabled[name]:
                            continue
                        nbrSales=sale[name]
                        # Exclude NaN values
                        if nbrSales == nbrSales and prod.getCommission()>0:
                            print("adding "+str(nbrSales*prod.getCommission())+" to "+name)
                            seller.addCommission(prod, nbrSales)
        
        # For each pack
        for index, row in sales_df.iterrows():
            # if product sold is Product
            pack = self.getPackage(pack_df, row['CÓDIGO'])
            if pack is not None:
                # add net commission each user
                for name, seller in seller_dc.items():
                    if pack.getCategory() not in self.categoriesEnabled[name]:
                        continue
                    nbrSales=row[name]
                    # Exclude NaN values
                    if nbrSales == nbrSales:
                        print("adding "+str(nbrSales*pack.getCommission())+" to "+name)
                        seller.addCommission(pack, nbrSales)
            

        print("Summary")
        for name, seller in seller_dc.items():
            print(name+" "+str(seller.getCommission()))
            seller.printSummary()
           
        return seller_dc

    def retrievePeriodTotalSales(self, beginDt, endDt):
        uri = "/stats/sales-statistics/?date__gte="+beginDt+"T05:00:00.000Z&date__lte="+endDt+"T04:59:59.999Z&page=1&business="+str(self.businessId)+"&time_unit=day"
        print(uri)
        rd = RequestHandler(uri)
        res = rd.execute()

        if res != None:
            return res['data']['total']
        else:
            print("Fail retrievePeriodTotalSales")
            sys.exit(1)
        
        
    def run(self, year:str, month:str):
        # Enter period
        if len(year)==0 or len(month)==0:
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

        # compute commission percentage from amaount of sales in the month
        amt = self.retrievePeriodTotalSales(beginDt, endDt)    
        self.commission = self.getCommissionPer(amt)
        print("Commision percent is:"+str(self.commission))

        repHeaders = ["CÓDIGO", "NOMBRE", "STOCK MÍNIMO", "CANTIDAD", "disable (EXTRA)",
                      "creado (EXTRA)", "CATEGORÍA", "PRECIO DE VENTA", "PRECIO DE COMPRA"]

        rd = ReportDownloader("Exportar productos.xlsx", "export_products",
                              repHeaders, beginDt, endDt, businessId=self.businessId)
        file1 = rd.execute()

        repHeaders = ["CÓDIGO", "NOMBRE", "DISABLE (PRODUCTO - EXTRA)",
                      "QANTUFARMA.JENNY (USUARIO)", "QANTUFARMA.RUTH (USUARIO)",
                      "QANTUFARMA.MIRIAM (USUARIO)", "QANTUFARMA.ROSANGELA2 (USUARIO)", "CANTIDAD TOTAL"]
        rd = ReportDownloader("Exportar ventas por producto.xlsx", "export_sales_per_product",
                              repHeaders, beginDt, endDt, businessId=self.businessId)
        file2 = rd.execute()

        #download package data
        repHeaders = ["CÓDIGO", "NOMBRE", "CÓDIGO (ITEM)", "NOMBRE (ITEM)", 
                      "CANTIDAD (ITEM)", "CATEGORÍA", "PRECIO DE VENTA", "ÚLTIMO PRECIO DE COMPRA"]
        rd = ReportDownloader("Exportar paquetes.xlsx", "export_packages",
                              repHeaders, beginDt, endDt, businessId=self.businessId)
        file3 = rd.execute()

        if file1=='' or file2=='' or file3=='':
            print("Faltan archivos")
            return None
        else:
            return self.summaryCommission(file1, file2, file3)


#cc = CommissionManager()
#cc.run()