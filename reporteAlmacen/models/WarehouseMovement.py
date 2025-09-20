from datetime import datetime

class WarehouseMovement:
    
    headers = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'OBS']
    
    def __init__(self, resp, typ:str='NO_TYPE'):
        self.user = resp['user']
        self.state = resp['is_active']
        self.obs = resp['observations']
        self.number = resp['number']
        self.date = resp['date']
        self.direction = resp['get_type_display']
        self.records = resp['records']
        self.moveType = typ
        self.data = []
        
    def getUser(self):
        return self.user
    
    def getState(self):
        return self.state
    
    def isActive(self):
        return self.state
    
    def getObs(self):
        return self.obs
    
    def getNumber(self):
        return self.number
    
    def getDate(self):
        return self.date
    
    def getDirection(self):
        return self.direction
    
    def getRecords(self):
        return self.records
    
    def getMoveType(self):
        return self.moveType
    
    def setMoveType(self, moveType):
        self.moveType = moveType
        
    def process(self):
        date = WarehouseMovement.formatDate(self.getDate())
        username = self.getUser()['username']
        number = self.getNumber()
        direction = self.getDirection()
        obs = self.getObs()
        
        self.data.append([date, username, number, direction, obs])
        return True
   
    def getData(self):
       return self.data
    
    @staticmethod
    def formatDate(dt):
        # Convertir a objeto datetime
        fecha_obj = datetime.fromisoformat(dt)
        # Formatear como deseas
        dateF = fecha_obj.strftime('%Y-%m-%d %H:%M')
        
        return dateF
