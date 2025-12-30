#Entity = dữ liệu thuần, không phụ thuộc framework
from dataclasses import dataclass
@dataclass
class Order:
    id:str
    lat:float
    lon:float
    