from fastapi import APIRouter, Depends, HTTPException, Query
from models.chemical import Chemical, Shelf
from db import chemicals_collection, shelves_collection
from services.utils import validate_bottle_number
from auth.auth_bearer import JWTBearer
from bson import ObjectId
from datetime import datetime

router = APIRouter()

# ──────────────── PUBLIC ROUTES ────────────────


@router.get("/")
def list_chemicals(skip: int = 0, limit: int = 50):
    pipeline = [
        {"$lookup": {
            "from": "shelves",
            "localField": "shelf_id",
            "foreignField": "_id",
            "as": "shelf"
        }},
        {"$unwind": {"path": "$shelf", "preserveNullAndEmptyArrays": True}},
        {"$skip": skip},
        {"$limit": limit}
    ]
    results = chemicals_collection.aggregate(pipeline)
    return [format_chemical_with_shelf(doc) for doc in results]


@router.get("/search/")
def search_chemicals(q: str = Query(...)):
    query = {
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"formula": {"$regex": q, "$options": "i"}},
            {"synonyms": {"$regex": q, "$options": "i"}},
            {"location": {"$regex": q, "$options": "i"}},
            {"bottle_number": {"$regex": q, "$options": "i"}},
        ]
    }
    pipeline = [
        {"$match": query},
        {"$lookup": {
            "from": "shelves",
            "localField": "shelf_id",
            "foreignField": "_id",
            "as": "shelf"
        }},
        {"$unwind": {"path": "$shelf", "preserveNullAndEmptyArrays": True}}
    ]
    results = chemicals_collection.aggregate(pipeline)
    return [format_chemical_with_shelf(doc) for doc in results]


@router.get("/formula/{formula}")
def get_by_formula(formula: str):
    pipeline = [
        {"$match": {"formula": formula}},
        {"$lookup": {
            "from": "shelves",
            "localField": "shelf_id",
            "foreignField": "_id",
            "as": "shelf"
        }},
        {"$unwind": {"path": "$shelf", "preserveNullAndEmptyArrays": True}}
    ]
    results = chemicals_collection.aggregate(pipeline)
    return [format_chemical_with_shelf(doc) for doc in results]


@router.get("/location/{location}")
def get_by_location(location: str):
    pipeline = [
        {"$match": {"location": location}},
        {"$lookup": {
            "from": "shelves",
            "localField": "shelf_id",
            "foreignField": "_id",
            "as": "shelf"
        }},
        {"$unwind": {"path": "$shelf", "preserveNullAndEmptyArrays": True}}
    ]
    results = chemicals_collection.aggregate(pipeline)
    return [format_chemical_with_shelf(doc) for doc in results]


@router.get("/next-bottle-number")
def next_bottle_number(shelf_id: str):
    try:
        shelf_object_id = ObjectId(shelf_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid shelf ID")
    
    shelf = shelves_collection.find_one({"_id": shelf_object_id})
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")
    
    prefix = shelf.get("shelfInitial", "")
    if not prefix:
        raise HTTPException(status_code=400, detail="Shelf has no initial defined")
    
    existing = list(chemicals_collection.find({
        "bottle_number": {"$regex": f"^{prefix}\\d{{3}}$"}
    }))
    used_numbers = sorted(
        int(doc["bottle_number"][len(prefix):]) for doc in existing
        if doc["bottle_number"].startswith(prefix) and doc["bottle_number"][len(prefix):].isdigit()
    )
    next_number = (used_numbers[-1] + 1) if used_numbers else 1
    return {"next_bottle_number": f"{prefix}{next_number:03}"}


@router.get("/stats/")
def get_statistics():
    total_chemicals = chemicals_collection.count_documents({})
    total_shelves = shelves_collection.count_documents({})
    shelfwise_count = shelves_collection.aggregate([
        {"$lookup": {
            "from": "chemicals",
            "localField": "_id",
            "foreignField": "shelf_id",
            "as": "chemicals"
        }},
        {"$project": {
            "shelf_name": "$name",
            "shelf_initial": "$shelfInitial",
            "chemical_count": {"$size": "$chemicals"}
        }}
    ])
    shelfwise_count = list(shelfwise_count)
    shelfwise_count = {shelf["shelf_name"]: shelf["chemical_count"] for shelf in shelfwise_count}
    return {
        "total_chemicals": total_chemicals,
        "total_shelves": total_shelves,
        "shelfwise_count": shelfwise_count
    }

# ──────────────── AUTHENTICATED ROUTES ────────────────


@router.post("/", dependencies=[Depends(JWTBearer())])
def create_chemical(chemical: Chemical):
    if validate_bottle_number(chemical.bottle_number):
        raise HTTPException(status_code=400, detail="Bottle number already exists")
    
    # Convert shelf_id to ObjectId
    if isinstance(chemical.shelf_id, str):
        try:
            chemical.shelf_id = ObjectId(chemical.shelf_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid shelf_id format")
    
    chemical_dict = chemical.model_dump()
    result = chemicals_collection.insert_one(chemical_dict)
    return {"id": str(result.inserted_id)}


@router.get("/{id}")
def get_chemical(id: str):
    try:
        object_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    pipeline = [
        {"$match": {"_id": object_id}},
        {"$lookup": {
            "from": "shelves",
            "localField": "shelf_id",
            "foreignField": "_id",
            "as": "shelf"
        }},
        {"$unwind": {"path": "$shelf", "preserveNullAndEmptyArrays": True}}
    ]
    
    result = list(chemicals_collection.aggregate(pipeline))
    if not result:
        raise HTTPException(status_code=404, detail="Chemical not found")
    
    return format_chemical_with_shelf(result[0])


@router.put("/{id}", dependencies=[Depends(JWTBearer())])
def update_chemical(id: str, chemical: Chemical):
    try:
        object_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    # Convert shelf_id to ObjectId
    if isinstance(chemical.shelf_id, str):
        try:
            chemical.shelf_id = ObjectId(chemical.shelf_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid shelf_id format")
    
    chemical_dict = chemical.model_dump()
    result = chemicals_collection.update_one(
        {"_id": object_id},
        {"$set": chemical_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chemical not found")
    return {"msg": "Updated successfully"}


@router.delete("/{id}", dependencies=[Depends(JWTBearer())])
def delete_chemical(id: str):
    try:
        object_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    result = chemicals_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chemical not found")
    return {"msg": "Deleted successfully"}


@router.get("/by-bottle/{bottle_number}")
def get_by_bottle_number(bottle_number: str):
    pipeline = [
        {"$match": {"bottle_number": bottle_number}},
        {"$lookup": {
            "from": "shelves",
            "localField": "shelf_id",
            "foreignField": "_id",
            "as": "shelf"
        }},
        {"$unwind": {"path": "$shelf", "preserveNullAndEmptyArrays": True}}
    ]
    
    result = list(chemicals_collection.aggregate(pipeline))
    if not result:
        raise HTTPException(status_code=404, detail="Chemical not found")
    
    return format_chemical_with_shelf(result[0])


@router.post("/validate-bottle", dependencies=[Depends(JWTBearer())])
def check_bottle_availability(bottle_number: str):
    exists = chemicals_collection.find_one({"bottle_number": bottle_number})
    return {"available": not bool(exists)}


@router.post("/shelves/", dependencies=[Depends(JWTBearer())])
def create_shelf(shelf: Shelf):
    shelf_dict = shelf.model_dump()
    shelf_dict["last_updated"] = datetime.now().isoformat()
    result = shelves_collection.insert_one(shelf_dict)
    return {"id": str(result.inserted_id), "msg": "Shelf created successfully"}


@router.get("/shelves/")
def list_shelves(skip: int = 0, limit: int = 50):
    cursor = shelves_collection.find().skip(skip).limit(limit)
    return [format_shelf(doc) for doc in cursor]


@router.get("/shelves/{id}")
def get_shelf(id: str):
    try:
        object_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid shelf ID format")
    
    shelf = shelves_collection.find_one({"_id": object_id})
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")
    return format_shelf(shelf)


@router.put("/shelves/{id}", dependencies=[Depends(JWTBearer())])
def update_shelf(id: str, shelf: Shelf):
    try:
        object_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid shelf ID format")
    
    shelf_dict = shelf.model_dump()
    shelf_dict["last_updated"] = datetime.now().isoformat()
    result = shelves_collection.update_one(
        {"_id": object_id},
        {"$set": shelf_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Shelf not found")
    return {"msg": "Shelf updated successfully"}


@router.delete("/shelves/{id}", dependencies=[Depends(JWTBearer())])
def delete_shelf(id: str):
    try:
        object_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid shelf ID format")
    
    result = shelves_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Shelf not found")
    return {"msg": "Shelf deleted successfully"}

# ──────────────── HELPER ────────────────

def format_chemical(doc):
    doc["id"] = str(doc["_id"])
    doc["shelf_id"] = str(doc["shelf_id"]) if "shelf_id" in doc else None
    doc["location"] = doc.get("location", "Unknown")
    del doc["_id"]
    return doc


def format_chemical_with_shelf(doc):
    result = format_chemical(doc)
    if "shelf" in doc:
        result["shelf"] = format_shelf(doc["shelf"])
    return result


def format_shelf(doc):
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

