import re
from datetime import datetime
import pandas
import math
from .QantuProduct import QantuProduct

class QantuSuplement(QantuProduct):
    def __init__(self, code, name, price, cost):
        super().__init__(code=code, name=name, category='SUPLEMENTOS',
                         price=price, cost=cost, commPer=0.1)