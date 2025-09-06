class WharehouseMovement:
    def __init__(self, resp):
        self.user = resp['user']
        self.state = resp['is_active']
        self.obs = resp['observations']
        self.number = resp['number']
        self.date = resp['date']
        self.direction = resp['get_type_display']
        self.records = resp['records']
        
        clss = WharehouseMovementClassifier(self)
        self.moveType = clss.getType()
        clss2 = AdjustClassifier(self)
        self.adjustType = clss2.getType()
        
    def getUser(self):
        return self.user
    
    def getState(self):
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
        
    def getAdjustType(self):
        return self.adjustType
        
    def getProduct(self):
        return self.records[0]
    
    
class WharehouseMovementClassifier:
    def __init__(self, move: WharehouseMovement):
        self.type = 'NO_TYPE'
        obser = move.getObs()
        
        if obser != None:
            obser=obser.upper()
                
            if 'USO INTERNO' in obser:
                self.type = 'INTERNAL_USE'
            elif 'TRASLADO' in obser:
                self.type = 'TRANSFER'
            elif all(palabra in obser for palabra in ['PRODUCTO', 'MOTIVO', 'CANTIDAD', 'MONTO']):
                self.type = 'ADJUST'
            elif 'VENCIDO' in obser:
                self.type = 'EXPIRED'
            else:
                self.type = 'NO_TYPE'
        
    def getType(self):
        return self.type
        

class AdjustClassifier:
    def __init__(self, move: WharehouseMovement):
        self.type = 'NO_TYPE'
        
        if move.getType()== 'ADJUST':
            
            obser = move.getObs()
        
            if obser != None:
                obser=obser.upper()
                
                if 'USO INTERNO' in obser:
                    self.type = 'INTERNAL_USE'
                elif 'TRASLADO' in obser:
                    self.type = 'TRANSFER'
                elif all(palabra in obser for palabra in ['PRODUCTO', 'MOTIVO', 'CANTIDAD', 'MONTO']):
                    self.type = 'ADJUST'
                elif 'VENCIDO' in obser:
                    self.type = 'EXPIRED'
                else:
                    self.type = 'NO_TYPE'
        
    def getType(self):
        return self.type
        
        