from pydantic import BaseModel
from typing import List
from datetime import datetime

class Chemical(BaseModel):
    name: str
    shelf_id: int  # This will reference the Shelf
    formula: str
    formula_latex: str
    synonyms: List[str] = []
    msds_url: str = ""
    structure_2d_url: str = ""
    bottle_number: str
    is_concentrated: bool = False


class Shelf(BaseModel):
    name: str
    location: str
    shelfInitial: str
    last_updated: str = datetime.now().isoformat()