class Price:
    def __init__(self, value, mcup=0.0, profitPer=0.0):
        self.value = value
        self.mcup = mcup
        self.profitPer = profitPer
        
    def getValue(self):
        return self.value
    
    def getMcup(self):
        return self.mcup
    
    def getProfitPer(self):
        return self.profitPer
    
    def setValue(self, value):
        self.value = value

class PriceManager:
    @classmethod
    def computePrice(cls, product):
        mcups = cls.computeMcup(product)
        gan_per = (mcups/(1-mcups))
        gan_per = round(gan_per, 4)
        presug = round((1+gan_per)*product.getLastCost(), 1)
        price = Price(presug, mcups, gan_per)
        #oldValuePrice = product.getPrice()
        #if oldValuePrice>price.getValue():
        #    price.setValue(oldValuePrice)
        return price
    
    @classmethod
    def computeProductBlisterPrice(cls, product):
        mcups = cls.computeMcup(product)
        cantidadItemBlis = int(product.getUnitsBlister())
        if cantidadItemBlis<=1:
            print("ERROR product["+product.getName()+"] has invalid unitsBlister.")
            return None
        dsct = 0.0
        if mcups>0.5:
            dsct = 0.3
        elif mcups>0.3:
            dsct = 0.1
        elif mcups>0.15:
            dsct = 0.05
        packPrice = round(product.getPrice()*cantidadItemBlis*(1-dsct), 1)
        price = Price(packPrice)
        return price
    
    @classmethod
    def computeProductCajaPrice(cls, product):
        mcups = cls.computeMcup(product)
        cantidadItemCja = int(product.getUnitsCaja())
        if cantidadItemCja<=1:
            print("ERROR product["+product.getName()+"] has invalid unitsCaja.")
            return None
        dsct = 0.0
        if mcups>0.7:
            dsct = 0.5
        if mcups>0.5:
            dsct = 0.3
        elif mcups>0.3:
            dsct = 0.1
        elif mcups>0.15:
            dsct = 0.05
        packPrice = round(product.getPrice()*cantidadItemCja*(1-dsct), 1)
        price = Price(packPrice)
        return price
        
    @classmethod
    def computeMcup(cls, product):
        mcups = 0.0
        if product.getCategory()=='MEDICAMENTOS':
            mcups = cls.mcupMedicamentos(product)
        else:
            mcups = cls.mcupGeneral(product)
            
        return mcups
    
    @staticmethod
    def mcupMedicamentos(prod):
        mcups = 0.0
        if prod.isGenerico():
            if prod.getFF() in ['TAB']:
                if prod.getLastCost()<=0.5:
                    mcups = 0.7
                elif prod.getLastCost()>0.5 and prod.getLastCost()<=0.8:
                    mcups = 0.67
                else:
                    mcups = 0.63
            else:
                mcups = 0.15
        else:
            if prod.getFF() in ['TAB']:
                mcups = 0.30
            else:
                mcups = 0.15
                
        return mcups
    
    @staticmethod
    def mcupGeneral(prod):
        mcups = 0.10
        return mcups
