import pandas
from datetime import datetime
from pathlib import Path
from models.WarehouseMovementFactory import WarehouseMovementFactory

class WarehouseMovementReport():
    
    def __init__(self, business:int, year:str, month:str):
        self.processed_move = []
        self.inactive_move = [] 
        self.business = business
        self.year = year
        self.month = month
        
    def process_movement(self, res)->int:
        move = WarehouseMovementFactory.createMovement(res)
        if move:
            if move.isActive():
                if move.process():
                    self.processed_move.append(move)
                else:
                    print("[ERROR] move can't be processed.")
                    return 2
            else:
                self.inactive_move.append(move)
                
            return 0
        else:
            print("[ERROR] Fail to create move.")
            return 1
        
        
        
    def generate_summary(self):
        # group move by types
        dictMoveByTypes = {}
        dictCrucesByNbr = {}
        for mov in self.processed_move:
            if mov.getMoveType()=='ADJUST' and mov.getMotive()=='CRUCE':
                dictCrucesByNbr[mov.getNumber()]=mov
            else:
                if not mov.getMoveType() in dictMoveByTypes:
                    dictMoveByTypes[mov.getMoveType()]=[]
                dictMoveByTypes[mov.getMoveType()].append(mov)
           
        # compund data
        dictDatByTypes = {}
        for typ in dictMoveByTypes:
            dictDatByTypes[typ]=[]
            for mov in dictMoveByTypes[typ]:
                dictDatByTypes[typ] += mov.getData()
        
        self.dictDfs = {}
        for typ in dictDatByTypes:
            self.dictDfs[typ]=pandas.DataFrame(dictDatByTypes[typ], columns = WarehouseMovementFactory.MOVEMENT_TYPE[typ].headers)
        
        # inactive movements
        inactiveData = []
        for move in self.inactive_move:
            inactiveData += move.getData()
        
        # Add inactive movements as 'inactive' type
        self.dictDfs['Inactive']=pandas.DataFrame(inactiveData, columns = WarehouseMovementFactory.MOVEMENT_TYPE['NO_TYPE'].headers)
        
        crossData = self.cross_movement_summarizer(dictCrucesByNbr)
        self.dictDfs['Cruces']=pandas.DataFrame(crossData, columns = WarehouseMovementFactory.MOVEMENT_TYPE['ADJUST'].headers)
    
    def export_report(self):
        now = datetime.now().strftime("%Y%m%d_%H%M")
        package_path = Path(__file__).parent.parent
        ruta_out = package_path / "out"
        # Crear el directorio si no existe
        #ruta_out.mkdir(exist_ok=True)
        fname = str(self.business)+'_'+self.year+self.month+'_'+'ReporteAlmacen_'+now+'.xlsx'
        excel_name = ruta_out / fname
        with pandas.ExcelWriter(excel_name) as excel_writer:
            for typ in self.dictDfs:
                self.dictDfs[typ].to_excel(excel_writer, sheet_name=typ, index=False)

    def cross_movement_summarizer(self, dictCross:dict):
        ls = []
        for nbr1, mov1 in dictCross.items():
            addFlag = False
            for nbr2, mov2 in dictCross.items():
                if mov2.isMatched():
                    continue
                print("nbr1="+str(nbr1)+" val2="+mov2.getNbrCross())
                if nbr1==int(mov2.getNbrCross()):
                    print("Set matched move")
                    mov1.setMatchedMove(mov2)
                    mov2.setMatchedMove(mov1)
                    addFlag = True
                    break
            print("Check if it's matched.")
            if mov1.isMatched() and addFlag:
                print("MATCHED!")
                ls+=mov1.getData()
                ls+=mov1.getMatchedMove().getData()
                ls+=mov1.getMatchedSummary()
            elif not mov1.isMatched():
                ls+=mov1.getData()
        return ls