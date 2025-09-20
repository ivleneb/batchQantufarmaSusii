from models.WarehouseMovement import WarehouseMovement

class InternalUseMovement(WarehouseMovement):
    
    headers = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'COD PROD', 'NOMBRE PROD', 'CANTIDAD']
    
    def __init__(self, data):
        super().__init__(data, 'INTERNAL_USE')

    def process(self):
        date = WarehouseMovement.formatDate(self.getDate())
        username = self.getUser()['username']
        number = self.getNumber()
        direction = self.getDirection()

        for rec in self.getRecords():
            self.data.append([date, username, number, direction, rec['product']['code'], rec['product']['name'], rec['quantity']])
        
        return True