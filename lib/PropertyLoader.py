import sys
sys.path.append(r'../')
import json

class PropertyLoader:
    
    @staticmethod
    def load():
        # Read JSON file
        with open('../lib/properties.json', 'r', encoding='utf-8') as file:
            dataCfg = json.load(file)
            return dataCfg
    
    @staticmethod
    def getSegCodes():
        return PropertyLoader.load()['seg_codes']
        
    @staticmethod
    def getRegCodePerCategory():
        return PropertyLoader.load()['reg_code_category']
    
    @staticmethod
    def getRegDigCodes():
        return PropertyLoader.load()['reg_dig_codes']