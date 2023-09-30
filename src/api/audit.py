from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    sql = """
    SELECT num_red_potions, num_red_ml, gold FROM global_inventory
    """
    with db.engine.begin() as connection:
        # Run the sql and returns a CursorResult object which represents the SQL results
        # Execute SQL statement to get num of red potions
        result = connection.execute(sqlalchemy.text(sql))
        first_row = result.first()
        num_red_potions_to_sell = first_row.num_red_potions() 
        ml_in_bottles = first_row.num_red_potions() 
        gold = first_row.num_red_potions() 
    return {"number_of_potions": num_red_potions_to_sell, "ml_in_barrels": ml_in_bottles, "gold": gold}

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
