from dataclasses import dataclass


@dataclass
class SKUItem:
    date: str
    catalog: str
    country: str
    name: str
    sku: str
    url: str
    available_sizes: int
    total_sizes: int
    semaforo: str
    page: int


@dataclass
class SizeStock:
    sku: str
    size: str
    units: int
    status: str
    is_available: bool
    semaforo: str
