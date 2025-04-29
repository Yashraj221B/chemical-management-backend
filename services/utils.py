import random
import string
from db import chemicals_collection

def generate_bottle_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

def validate_bottle_number(bottle_number: str):
    return chemicals_collection.find_one({"bottle_number": bottle_number}) is not None