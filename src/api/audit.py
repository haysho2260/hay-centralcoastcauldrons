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
    sql1 = "SELECT COALESCE(SUM(num_red_ml + num_green_ml + num_blue_ml + num_dark_ml),0) AS total_ml, COALESCE(SUM(gold),0) AS sum_gold FROM global_inventory;"
    sql2 = "SELECT COALESCE(SUM(quantity),0) AS total_potions FROM potions_inventory;"
    # Execute the query
    # see how much num_ml & num_potions we have
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql1)).first()
        total_potions = connection.execute(sqlalchemy.text(sql2)).scalar_one()
    
        print(f"get_inventory: total_ml {result.total_ml}")
        print(f"get_inventory: total_potions {total_potions}")

    return {"number_of_potions": total_potions, "ml_in_barrels": result.total_ml, "gold": result.sum_gold}

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
