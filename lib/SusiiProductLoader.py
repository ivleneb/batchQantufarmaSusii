import sys, os
sys.path.append(r'../')
from lib.QantuMedicine import QantuMedicine
from lib.QantuGalenico import QantuGalenico
from lib.QantuDevice import QantuDevice
from lib.QantuGeneral import QantuGeneral
from lib.QantuPackage import QantuPackage
from lib.QantuProduct import QantuProduct
from lib.ReportDownloader import ReportDownloader
import pandas
from datetime import datetime
import json
import numpy as np
import shutil


class SusiiProductLoader:
    def __init__(self, businessId):
        self.businessId = businessId
        self.prodSale_df = None
        self.productDict = None
        
    def setBusinessId(self, businessId):
        self.businessId = businessId
        
    def getBusinessId(self):
        return self.businessId
    
    def downloadProducts(self, downloadSaleData:bool=False, backup:bool=False):
        today = datetime.now().strftime("%Y-%m-%d")
        #prodSale_df = None
        if downloadSaleData and self.prodSale_df is None:
            self.downloadSaleData()
            
        # download product data
        repHeaders = ["CÓDIGO", "NOMBRE", "ALIAS", "UNIDAD", "PRECIO DE VENTA", "PRECIO DE COMPRA", "CANTIDAD",
                "num_regsan (EXTRA)", "lab (EXTRA)", "disable (EXTRA)", "creado (EXTRA)", "generico (EXTRA)", "fecha_vto (EXTRA)",
                "nro_lote (EXTRA)", "adicional (EXTRA)", "otc (EXTRA)", "temp_alm (EXTRA)", "units_blister (EXTRA)",
                "units_caja (EXTRA)", "tipo_tratamiento (EXTRA)", "price_logic (EXTRA)", "seg_1 (EXTRA)", "seg_2 (EXTRA)", "seg_3 (EXTRA)",
                "MONEDA DE VENTA", "MONEDA DE COMPRA", "CON STOCK", "CATEGORÍA",
                "IMPUESTO", "PESO BRUTO (KGM)", "STOCK MÍNIMO", "PORCENTAJE DE GANANCIA", "DESCUENTO", "TIPO DE DESCUENTO",
                "BÚSQUEDA DESDE VENTAS", "CATEGORÍA SUNAT"]
        
        
        rd = ReportDownloader("Exportar productos.xlsx", "export_products",
                              repHeaders, '2024-02-12',
                              today, businessId=self.businessId)
        file_prod = rd.execute()
        if file_prod == "":
            sys.exit("Can't dowloand file[Exportar productos.xlsx]")
        
        if backup:
            self.makeBackup(file_prod)
        
        prod_df = pandas.read_excel(file_prod, skiprows=4)
        print("REG SIZE (prod):"+str(len(prod_df)))

        self.validateProductDf(prod_df)

        #pack_df = pandas.read_excel(file_pack, skiprows=4)
        #print("REG SIZE (prod):"+str(len(prod_df)))

        # Load products
        productDict:dict[str, QantuProduct] = {}
        for index, row in prod_df.iterrows():
            # only add sales that are products
            prod = self.getProduct(prod_df, row['CÓDIGO'])
            if prod is not None and not prod.isDisable():
                # add product to data dict
                if prod.getCode() in productDict:
                    raise Exception("FATAL Index["+str(index)+"] Key must be unique")
                if downloadSaleData:
                    self.addSaleData(prod, self.prodSale_df)
                productDict[prod.getCode()]=prod
        
        self.productDict = productDict
                    
        return productDict
    
    def downloadPackages(self, downloadSaleData:bool=False, backup:bool=False):
        today = datetime.now().strftime("%Y-%m-%d")
        
        if self.productDict is None:
            self.downloadProducts(downloadSaleData)
        
        if downloadSaleData and self.prodSale_df is None:
            self.downloadSaleData()
            
        #repHeaders = ["CÓDIGO", "NOMBRE", "CÓDIGO (ITEM)", "NOMBRE (ITEM)", 
        #          "CANTIDAD (ITEM)"]
        repHeaders = ["CÓDIGO", "NOMBRE", "ALIAS", "UNIDAD", "PRECIO DE VENTA", "CATEGORÍA", "CÓDIGO (ITEM)", "NOMBRE (ITEM)",
              "ALIAS (ITEM)", "UNIDAD (ITEM)", "PRECIO DE VENTA (ITEM)", "CANTIDAD (ITEM)"]
        rd = ReportDownloader("Exportar paquetes.xlsx", "export_packages",
                          repHeaders, '2024-02-12',
                          today)
        file_pack = rd.execute()
        if file_pack == "":
            sys.exit("Can't dowloand file[Exportar productos.xlsx]")
            
        if backup:
            self.makeBackup(file_pack)
            
        pack_df = pandas.read_excel(file_pack, skiprows=4)
        print("REG SIZE (prack):"+str(len(pack_df)))
        
        # Load packages
        packDict:dict[str, QantuPackage] = {}
        #for index, row in self.prodSale_df.iterrows():
            # only add sales that are products
            #pack = self.getPackage(pack_df, row['CÓDIGO'])
            #if pack is not None:
                #pack.setSoldUnits(row['CANTIDAD TOTAL'])
                #packDict[pack.getCode()]=pack
                
        for key, row in pack_df.iterrows():
            # only add sales that are products
            pack = self.getPackage(self.productDict, pack_df, row['CÓDIGO'])
            if not (pack is None):
                packDict[pack.getCode()]=pack
                if self.prodSale_df is not None:
                    self.addPackageSaleData(pack, self.prodSale_df)
        return packDict
    
    
    def downloadSaleData(self):
        today = datetime.now().strftime("%Y-%m-%d")
        # download sales per product
        repHeaders = ["CÓDIGO", "NOMBRE", "STOCK ACTUAL",
                      "ÚLTIMO PROVEEDOR", "CANTIDAD TOTAL"]
        rd = ReportDownloader("Exportar ventas por producto.xlsx", "export_sales_per_product",
                              repHeaders, '2023-05-27',
                              today)
        file_sales = rd.execute()
        if file_sales == "":
            sys.exit("Can't dowloand file[Exportar ventas por producto.xlsx]")
        
        self.prodSale_df = pandas.read_excel(file_sales, skiprows=5)
        print("REG SIZE (prod sales):"+str(len(self.prodSale_df)))
    
        
    def cobineProducts(self, prodDict):
        prodDict=combineMedicines(prodDict)
        prodDict=combineGalenicos(prodDict)
        prodDict=combineMedDevices(prodDict)
        
        return prodDict
    
    def getProduct(self, prod_df, code):
        sub_df = prod_df.loc[prod_df['CÓDIGO'] == code]
        if len(sub_df)==1:
            row = sub_df.iloc[0]
            prod = None
            if row['CATEGORÍA']=='MEDICAMENTOS':
                prod = QantuMedicine(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'],
                                     row['disable (EXTRA)'], row['creado (EXTRA)'], row['STOCK MÍNIMO'])
            elif row['CATEGORÍA']=='GALENICOS':
                prod = QantuGalenico(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'],
                                     row['disable (EXTRA)'], row['creado (EXTRA)'], row['STOCK MÍNIMO'])
            elif row['CATEGORÍA']=='DISPOSITIVOS MEDICOS':
                prod = QantuDevice(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'],
                                   row['disable (EXTRA)'], row['creado (EXTRA)'], row['STOCK MÍNIMO'])
            else:
                prod = QantuGeneral(row['CÓDIGO'], row['NOMBRE'], row['CANTIDAD'],
                                    row['disable (EXTRA)'], row['CATEGORÍA'], row['creado (EXTRA)'],
                                    row['STOCK MÍNIMO'])
            # add data
            #"CÓDIGO",
            #"NOMBRE"
            prod.setAlias(row["ALIAS"])
            prod.setUnidad(row["UNIDAD"])
            prod.setPrice(row['PRECIO DE VENTA'])
            prod.setLastCost(row['PRECIO DE COMPRA'])
            #"CANTIDAD",
            prod.setNumRegSan(row["num_regsan (EXTRA)"])
            prod.setBrand(row["lab (EXTRA)"])
            #"disable (EXTRA)",
            #"creado (EXTRA)",
            prod.setGenerico(row['generico (EXTRA)'])
            prod.setFechaVto(row["fecha_vto (EXTRA)"])
            prod.setNroLote(row["nro_lote (EXTRA)"])
            prod.setAdicional(row["adicional (EXTRA)"])
            prod.setOtc(row["otc (EXTRA)"])
            prod.setTempAlm(row["temp_alm (EXTRA)"])
            prod.setUnitsBlister(row["units_blister (EXTRA)"])
            prod.setUnitsCaja(row["units_caja (EXTRA)"])
            prod.setTipoTratamiento(row["tipo_tratamiento (EXTRA)"])
            prod.setPriceLogic(row["price_logic (EXTRA)"])
            prod.setSeg1(row["seg_1 (EXTRA)"])
            prod.setSeg2(row["seg_2 (EXTRA)"])
            prod.setSeg3(row["seg_3 (EXTRA)"])
            prod.setMonedaDeVenta(row["MONEDA DE VENTA"])
            prod.setMonedaDeCompra(row["MONEDA DE COMPRA"])
            prod.setConStock(row["CON STOCK"])
            #"CATEGORÍA"
            prod.setImpuesto(row["IMPUESTO"])
            prod.setPesoBruto(row["PESO BRUTO (KGM)"])
            #"STOCK MÍNIMO"
            prod.setPorcentajeDeGanancia(row["PORCENTAJE DE GANANCIA"])
            prod.setDescuento(row["DESCUENTO"])
            prod.setTipoDeDescuento(row["TIPO DE DESCUENTO"])
            prod.setBusquedaDesdeVentas(row["BÚSQUEDA DESDE VENTAS"])
            prod.setCategoriaSunat(row["CATEGORÍA SUNAT"])
            
            return prod
        
        elif len(sub_df)==0:
            print("Product not found")
            return None
        else:
            raise Exception("Code with multiple products.")
    
    def getPackage(self, prodDict, pack_df, code):
        sub_df = pack_df.loc[pack_df['CÓDIGO'] == code]
        if len(sub_df)>0:
            row = sub_df.iloc[0]
            pack = QantuPackage(row['CÓDIGO'], row['NOMBRE'], row['PRECIO DE VENTA'],
                                category=row['CATEGORÍA'], alias=row['ALIAS'], unidad=row['UNIDAD'])
            cost = 0
            pName = pack.getName()
            for index, row in sub_df.iterrows():
                #print(f"Adding {row['NOMBRE (ITEM)']} X {row['CANTIDAD (ITEM)']} to {row['NOMBRE']}")
                cantItem = row['CANTIDAD (ITEM)']
                codeItem = row['CÓDIGO (ITEM)']
                pack.addItem(codeItem, cantItem)
                if codeItem in prodDict:
                    prod = prodDict[codeItem]
                    pack.addItemObj(prod)
                    cost=cost+cantItem*prod.getLastCost()
                    if prod.getCategory()=='MEDICAMENTOS':
                        pack.setGenerico(prod.isGenerico())
                else:
                    print(f"WARN index={index} Package {code}[{pName}] item not found {codeItem}")
                
            pack.setCost(cost)
            return pack
        else:
            #print(f"Package {code} not found, invalid or deleted")
            return None
    
    def isNumeric(self, col, df):
        if col in df.columns:
            es_numerica = pandas.api.types.is_numeric_dtype(df[col])
            return es_numerica
        else:
            return False
    
    def validateProductDf(self, prod_df):
        if not self.isNumeric('disable (EXTRA)', prod_df):
            print("Columna 'disable (EXTRA)' tiene valores no numéricos.")
            sys.exit(1)
        else:
            prod_df["disable (EXTRA)"] = prod_df["disable (EXTRA)"].fillna(0)
        
        if not self.isNumeric('generico (EXTRA)', prod_df):
            print("Columna 'generico (EXTRA)' tiene valores no numéricos.")
            sys.exit(1)
        else:
            prod_df["generico (EXTRA)"] = prod_df["generico (EXTRA)"].fillna(0)

        if not self.isNumeric('units_blister (EXTRA)', prod_df):
            print("Columna 'units_blister (EXTRA)' tiene valores no numéricos.")
            sys.exit(2)
        else:
            prod_df["units_blister (EXTRA)"] = prod_df["units_blister (EXTRA)"].fillna(0)

        if not self.isNumeric('units_caja (EXTRA)', prod_df):
            print("Columna 'units_caja (EXTRA)' tiene valores no numéricos.")
            sys.exit(3)
        else:
            prod_df['units_caja (EXTRA)'] = prod_df['units_caja (EXTRA)'].fillna(0)
        
        if not self.isNumeric("price_logic (EXTRA)", prod_df):
            print("Columna 'price_logic (EXTRA)' tiene valores no numéricos.")
            sys.exit(4)
        else:
            prod_df["price_logic (EXTRA)"] = prod_df["price_logic (EXTRA)"].fillna(1)
        
        prod_df["nro_lote (EXTRA)"] = prod_df["nro_lote (EXTRA)"].fillna("")

        if not self.isNumeric('tipo_tratamiento (EXTRA)', prod_df):
            print("Columna 'tipo_tratamiento (EXTRA)' tiene valores no numéricos.")
            #sys.exit(1)
        else:
            prod_df["tipo_tratamiento (EXTRA)"] = prod_df["tipo_tratamiento (EXTRA)"].fillna(0)
    
    def addSaleData(self, prod, sale_df):
        sub_df = sale_df.loc[sale_df['CÓDIGO'] == prod.getCode()]
        if len(sub_df)==1:
            row = sub_df.iloc[0]
            # add sale data
            prod.setSoldUnits(row['CANTIDAD TOTAL'])
            # add provider data
            if type(row['ÚLTIMO PROVEEDOR'])!=float and len(row['ÚLTIMO PROVEEDOR'])!=0:
                prod.setLastProvider(row['ÚLTIMO PROVEEDOR'])
            else:
                prod.setLastProvider(self.defaultProviders(prod))
        elif len(sub_df)==0:
            if(prod.getActiveDays()>90 and prod.getStock()>0):
                print("Product ["+prod.getName()+"] never sale!")
            prod.setSoldUnits(0)
            prod.setLastProvider(self.defaultProviders(prod))
        else:
            print(sub_df)
            print("Code with multiple products.")
            print("Consider accumulated.")
            lastProv=""
            soldUnits=0
            for i in range(len(sub_df)):
                
                row = sub_df.iloc[i]
                print(row['NOMBRE'])
                
                if type(row['ÚLTIMO PROVEEDOR'])!=float and len(row['ÚLTIMO PROVEEDOR'])!=0:
                    lastProv=row['ÚLTIMO PROVEEDOR']
                else:
                    lastProv=self.defaultProviders(prod)
                    
                soldUnits+=row['CANTIDAD TOTAL']
            # add sale data
            prod.setLastProvider(lastProv)
            #prod.setLastCost(row['ÚLTIMO PRECIO DE COMPRA'])
            #prod.setPrice(row['ACTUAL PRECIO DE VENTA'])
            prod.setSoldUnits(soldUnits)
            #if prod.getLastProvider() is None or len(prod.getLastProvider())==0:
            #    prod.setLastProvider(self.defaultProviders(prod))
            #raise Exception("Code with multiple products.")
            
    def addPackageSaleData(self, pack, prodSale_df):
        sub_df = prodSale_df.loc[prodSale_df['CÓDIGO'] == pack.getCode()]
        if len(sub_df)==1:
            row = sub_df.iloc[0]
            pack.setSoldUnits(row['CANTIDAD TOTAL'])
        elif len(sub_df)==0:
            pack.setSoldUnits(np.int64(0))
        else:
            print("FATAL conflict more than 1 records for package in prodSale:"+ row['CÓDIGO'])
            raise ValueError("more than 1 records for package in prodSale")

    def defaultProviders(self, prod):
        if prod.getCategory() in ['MEDICAMENTOS', 'SUPLEMENTOS']:
            return "V&G pref"
        elif prod.getCategory()=='LIMPIEZA':
            return "VEGA pref"
        elif prod.getCategory()=='OFICINA':
            return "OFICINA pref"
        elif prod.getCategory()=='WEARABLES':
            return "ELECTRO pref"
        elif prod.getCategory()=='ALIMENTOS' and 'CHOCO' in prod.getName():
            return "LINAJE pref"
        elif prod.getCategory()=='ALIMENTOS' and (not 'CHOCO' in prod.getName() and not 'ACEITE' in prod.getName()):
            return "UNION pref"
        elif prod.getCategory()=='ADULTO MAYOR':
            return "CBC pref"
        else:
            return "LIMACENTER pref"
    
    def makeBackup(self, archivo_origen):
        now = datetime.now().strftime("%Y%m%d")
        archivo_destino = "bkp_"+now+"_"+archivo_origen

        # Crear directorio de destino si no existe
        directorio_destino = "backups"
        if not os.path.exists(directorio_destino):
            os.makedirs(directorio_destino)
        
        fullpath = os.path.join(directorio_destino, archivo_destino)
        try:
            shutil.copy(archivo_origen, fullpath)
            print(f"Archivo copiado de {archivo_origen} a {fullpath}")
        except FileNotFoundError:
            print(f"Error: El archivo {archivo_origen} no existe")
        except PermissionError:
            print("Error: No tienes permisos para leer/escribir")
