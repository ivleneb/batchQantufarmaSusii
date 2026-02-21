from models.WarehouseMovement import WarehouseMovement

class AdjustMovement(WarehouseMovement):
    
    headers = ['FECHA', 'USUARIO', 'NRO MOV', 'DIR', 'COD PROD', 'NOMBRE PROD', 'CANTIDAD', 'MOTIVO', 'COSTO', 'COMENTARIOS', 'OBS']
    
    def __init__(self, data):
        super().__init__(data, 'ADJUST')
        self.buildProperties(data)
        
    def buildProperties(self, data):
        self.product = data['records'][0]['product']
        self.pCode = self.product['code']
        self.pName = self.product['name']
        self.recQtty = data['records'][0]['quantity']
        self.motive = ''
        self.cost = ''
        self.quant = ''
        self.nro = ''
        self.comm = ''
        self.matched = None
        self.costFinal = 0.0
        
        obs = self.getObs()
        #obs = obs.upper()
        obsLsDirty = obs.split('\n')
        obsLsSpaces = [ elem for elem in obsLsDirty if elem != '' ]
        obsLs = [ elem.replace(" ", "") for elem in obsLsSpaces ]
        
        if len(obsLs)!=4 and len(obsLs)!=5:
            comm = "[WARNING] AJUSTE "+str(self.number)+": OBSERVACION NO CUMPLE EL FORMATO:"+obs+"\n"
            print(comm)
            self.comm += comm
            return
        
        for i in range(len(obsLs)):
            if self.pCode in obsLs[i]:
                try:
                    motiveStr = obsLs[i+1].upper()
                    if 'MOTIVO' in motiveStr:
                        motiveLs = motiveStr.split(':')
                        self.motive = motiveLs[1]
                    else:
                        comm += "[WARNING] Literal 'MOTIVO' not present in "+motiveStr+"\n"
                        print(comm)
                        self.comm += comm
                        return
                    
                    quantStr = obsLs[i+2].upper()
                    if 'CANTIDAD' in quantStr:
                        quantLs = quantStr.split(':')
                        self.quant = quantLs[1]
                    else:
                        comm = "[WARNING] Literal 'CANTIDAD' not present in "+quantStr+"\n"
                        print(comm)
                        self.comm += comm
                        return
                    
                    costStr = obsLs[i+3].upper()
                    if 'MONTO' in costStr:
                        costLs = costStr.split(':')
                        self.cost = costLs[1]
                    else:
                        comm = "[WARNING] Literal 'MONTO' not present in "+costStr+"\n"
                        print(comm)
                        self.comm += comm
                        return
                    
                    if 0<= i+4 <len(obsLs):
                        nroStr = obsLs[i+4].upper()
                        if 'NRO' in nroStr:
                            nroLs = nroStr.split(':')
                            self.nro = nroLs[1]
                        else:
                            comm = "[WARNING] Literal 'NRO' not present in "+costStr+"\n"
                            print(comm)
                            self.comm += comm
                            return
                    
                    return 
                except IndexError as e:
                    comm = f"[WARNING] Error: {e}"
                    print(comm)
                    self.comm += comm
                finally:
                    return 
        
        comm = "[WARNING] Product code "+self.pCode+" not found!"
        print(comm)
        self.comm += comm
        return

    def gerProduct(self):
        return self.records[0]
    
    def getMotive(self):
        return self.motive
        
    def getQtty(self):
        return self.qtty
        
    def getAmount(self):
        return self.amount
        
    def process(self):
        date = WarehouseMovement.formatDate(self.getDate())
        username = self.getUser()['username']
        number = self.getNumber()
        direction = self.getDirection()
        obs = self.getObs()
        
        self.data = []
            
        if '' in [self.motive, self.cost, self.quant]:
            #print([motive, cost, quant])
            comm = "[WARNING] AJUSTE "+str(number)+": getInfoAdjust for "+str(self.pCode)+" retornó valores inválidos."
            print(comm)
            self.comm += comm
            self.data.append([date, username, number, direction, self.pCode, self.pName, self.quant, self.motive, 0.0, self.comm, obs])
            return True
        
        if float(self.quant) != float(self.recQtty):
            comm = "[WARNING] AJUSTE "+str(number)+": CANTIDAD DE PRODUCTO "+str(self.pCode)+" NO COINCIDE CON OBS. ("+self.quant+"!="+self.recQtty+")"
            print(comm)
            self.comm+=comm
            self.data.append([date, username, number, direction, self.pCode, self.pName, self.quant, self.motive, 0.0, self.comm, obs])
            return True
            
        costF = float(self.cost)
        self.costFinal = round(costF, 2)
        msg = ''
        if costF > 0.0 and direction=='Salida':
            msg = 'Revisar signo'
        elif costF < 0.0 and direction=='Entrada':
            msg = 'Revisar signo'
        self.comm+=msg
        self.data.append([date, username, number, direction, self.pCode, self.pName, self.quant, self.motive, self.costFinal, self.comm, obs])

        return True
        
    def getNbrCross(self):
        return self.nro
        
    def setMatchedMove(self, mov):
        self.matched = mov
     
    def getMatchedMove(self):
        return self.matched
        
    def isMatched(self):
        return self.matched != None
    
    def getCostFinal(self):
        return self.costFinal
    
    def getMatchedSummary(self):
        
        if not self.isMatched():
            print("[WARNING] Adjust ["+self.getNumber()+"] not matched.")
            return []
        
        dat = []
        bal = self.getCostFinal()+self.matched.getCostFinal()
        if bal>0.0:
            bal = 0.0
        
        dat.append(['', '', '', '', '', 'BALANCE', '', '', bal, '', ''])
        return dat