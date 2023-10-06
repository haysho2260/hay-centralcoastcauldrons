from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db
from src.api.temp_dict import colors
from fastapi import HTTPException

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    total_potions = 0
    total_ml = 0
    for color in colors:
            # Define the SQL query with placeholders for color
            sql = """
                SELECT num_{}_ml, num_{}_potions FROM global_inventory
            """

            # Replace the placeholders with the actual color value
            formatted_sql = sql.format(color, color)

            # Execute the query
            # see how much num_ml & num_potions we have
            with db.engine.begin() as connection:
                num_ml_have, num_potions_have = connection.execute(sqlalchemy.text(formatted_sql)).first()
            
                print(f"get_inventory: potion num_{color}_ml_have {num_ml_have}")
                print(f"get_inventory: potion num_{color}_potions_have {num_potions_have}")
                
                total_potions += num_potions_have
                total_ml += num_ml_have
    
    print(f"get_inventory: total_potions {total_potions}")
    print(f"get_inventory: total_ml {total_ml}")       
    gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
    print(f"get_inventory: gold {gold}")
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": gold}

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
