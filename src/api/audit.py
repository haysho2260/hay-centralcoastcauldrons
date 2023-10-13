from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db
from fastapi import HTTPException

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():

    # Define the SQL query with placeholders for color
    sql = """
        SELECT num_red_ml + num_green_ml + num_blue_ml + num_dark_ml AS total_ml, gold FROM global_inventory;
        SELECT SUM(quantity) AS total_potions FROM potion_catalog
    """
    # Execute the query
    # see how much num_ml & num_potions we have
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql)).first()
    
        print(f"get_inventory: total_ml {result.total_ml}")
        print(f"get_inventory: total_potions {result.total_potions}")

    return {"number_of_potions": result.total_potions, "ml_in_barrels": result.total_ml, "gold": result.gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
