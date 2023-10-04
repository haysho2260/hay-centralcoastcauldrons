from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            # see how much red ml left
            num_red_ml_have = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).first().num_red_ml
            # add amount of red ml
            num_red_ml_added = barrel.ml_per_barrel * barrel.quantity
            # update in db
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {num_red_ml_have + num_red_ml_added}"))
            # find amount gold, find amount used, update db
            num_gold_have = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first().gold
            num_gold_used = barrel.price * barrel.quantity
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {num_gold_have -  num_gold_used}"))
            
            print(f"post_deliver_barrels: num_red_ml_have {num_red_ml_have}")
            print(f"post_deliver_barrels: num_red_ml_added {num_red_ml_added}")
            print(f"post_deliver_barrels: num_gold_have {num_gold_have}")
            print(f"post_deliver_barrels: num_gold_used {num_gold_used}")
           
        
    print(barrels_delivered)
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    plan = []
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
    first_row = result.first()
    num_gold = first_row.gold
    print(f"get_wholesale_purchase_plan: num_gold {num_gold}")
    for barrel in wholesale_catalog:
        barrels_to_buy = 0
        if barrel.sku == "SMALL_RED_BARREL":
            if num_gold >= 10:
                barrels_to_buy = num_gold // barrel.price
                num_gold = num_gold - (barrels_to_buy * barrel.price)
                print(f"get_wholesale_purchase_plan: num_gold {num_gold}")
                print(f"get_wholesale_purchase_plan: barrels_to_buy {barrels_to_buy}")
                plan.append({"sku":barrel.sku, "quantity":barrels_to_buy})
            

    return plan
