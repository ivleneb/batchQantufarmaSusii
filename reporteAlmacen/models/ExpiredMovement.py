from models.WarehouseMovement import WarehouseMovement

class ExpiredMovement(WarehouseMovement):
    
    headers = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'COD PROD', 'NOMBRE PROD', 'CANTIDAD', 'COSTO VENTA', 'COSTO COMPRA']
    
    def __init__(self, data):
        super().__init__(data, 'EXPIRED')

    def process(self):
        date = WarehouseMovement.formatDate(self.getDate())
        username = self.getUser()['username']
        number = self.getNumber()
        direction = self.getDirection()

 
        for rec in self.getRecords():
            costBuy = 0.0
            sellPrice = rec['product']['selling_price']
            buyPrice = rec['product']['last_buy_price']
            if buyPrice != None:
                costBuy = float(rec['quantity'])*float(buyPrice)
            costSale = 0.0
            if sellPrice != None:
                costSale = float(rec['quantity'])*float(sellPrice)
            self.data.append([date, username, number, direction, rec['product']['code'], rec['product']['name'], rec['quantity'], -costSale, -costBuy])
        
        return True