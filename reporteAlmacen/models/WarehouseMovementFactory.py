from typing import Dict, Any, Optional, Type
from models.WarehouseMovement import WarehouseMovement
from models.TransferMovement import TransferMovement
from models.AdjustMovement import AdjustMovement
from models.InternalUseMovement import InternalUseMovement
from models.ExpiredMovement import ExpiredMovement

class WarehouseMovementFactory:
    
    MOVEMENT_TYPE = {
        'INTERNAL_USE': InternalUseMovement,
        'TRANSFER': TransferMovement,
        'ADJUST': AdjustMovement,
        'EXPIRED': ExpiredMovement,
        'NO_TYPE': WarehouseMovement
        }
    
    @classmethod
    def createMovement(cls, movement_data: Dict[str, Any])->Optional[WarehouseMovement]:
        move_type = cls.determineMovementType(movement_data)
        
        if move_type in cls.MOVEMENT_TYPE:
            move_class = cls.MOVEMENT_TYPE[move_type]
            return move_class(movement_data)    
                    
        print(f"[WARNING] Tipo de moviminto desconocido: {move_type}")
        return None
    
    @staticmethod
    def determineMovementType(movement_data: Dict[str, Any])->str:
        typ = ''
        if 'observations' in movement_data:
            obser = movement_data['observations']
            
            if obser != None:
                obser=obser.upper()
                    
                if 'USO INTERNO' in obser:
                    typ = 'INTERNAL_USE'
                elif 'TRASLADO' in obser:
                    typ = 'TRANSFER'
                elif all(palabra in obser for palabra in ['PRODUCTO', 'MOTIVO', 'CANTIDAD', 'MONTO']):
                    typ = 'ADJUST'
                elif 'VENCIDO' in obser:
                    typ = 'EXPIRED'
                else:
                    typ = 'NO_TYPE'
            else:
                typ = 'NO_TYPE'
        else:
            typ = 'INVALID'
        
        return typ
        
