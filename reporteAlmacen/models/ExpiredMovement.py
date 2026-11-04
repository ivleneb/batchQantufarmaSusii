from models.WarehouseMovement import WarehouseMovement
from lib.RequestHandler import RequestHandler

class ExpiredMovement(WarehouseMovement):
    
    headers = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'COD PROD', 'NOMBRE PROD', 'CANTIDAD', 'COSTO VENTA', 'COSTO COMPRA']
    
    def __init__(self, data):
        super().__init__(data, 'EXPIRED')
        self.businessId = data.get('business')
        
    def getProductPrices(self):
        records = self.getRecords()
        # Obtener IDs únicos de los productos del movimiento
        product_ids = list({
            str(rec['product']['id'])
            for rec in records
            if rec.get('product') and rec['product'].get('id') is not None
        })
        if not product_ids:
            return {}
        ids = ','.join(product_ids)
        uri = (f"/v1/products/products/?ids={ids}&business={self.businessId}&page=1&include_disabled_products=true")
        handler = RequestHandler(uri, businessId=self.businessId)
        response = handler.execute()
        # Organizar productos por ID para encontrarlos rápidamente
        products = response.get('items', [])
        return {
            str(product['id']): product
            for product in products
        }

    def process(self):
        date = WarehouseMovement.formatDate(self.getDate())
        username = self.getUser()['username']
        number = self.getNumber()
        direction = self.getDirection()
        product_prices = self.getProductPrices()
 
        for rec in self.getRecords():
            product = rec['product']
            product_id = str(product['id'])
            product_info = product_prices.get(product_id, {})
            costBuy = 0.0
            sellPrice = product_info.get('selling_price')
            buyPrice = product_info.get('last_buy_price')
            
            if buyPrice is not None:
                costBuy = float(rec['quantity'])*float(buyPrice)
            costSale = 0.0
            if sellPrice != None:
                costSale = float(rec['quantity'])*float(sellPrice)
            self.data.append([date, username, number, direction, product['code'], product['name'], rec['quantity'], -costSale, -costBuy])
        
        return True