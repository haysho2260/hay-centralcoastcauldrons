from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from fastapi import HTTPException


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
    print(f"post_deliver_barrels: barrels_delivered {barrels_delivered}")
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:

            if "red" in barrel.sku.lower():
                color = "red"
            elif "green" in barrel.sku.lower():
                color = "green"
            elif "blue" in barrel.sku.lower():
                color = "blue"
            else:
                raise HTTPException(status_code=404, detail=f"{barrel.sku} barrel not found")
            # see how much red ml left
            num_ml_have = connection.execute(sqlalchemy.text("SELECT num_{color}_ml FROM global_inventory")).scalar()
            # add amount of red ml
            num_ml_added = barrel.ml_per_barrel * barrel.quantity
            # update in db
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_{color}_ml = {num_ml_have + num_ml_added}"))
            # find amount gold, find amount used, update db
            num_gold_have = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first().gold
            num_gold_used = barrel.price * barrel.quantity
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {num_gold_have -  num_gold_used}"))
            
            print(f"post_deliver_barrels: num_{color}_ml_have {num_ml_have}")
            print(f"post_deliver_barrels: num_{color}_ml_added {num_ml_added}")
            print(f"post_deliver_barrels: num_gold_have {num_gold_have}")
            print(f"post_deliver_barrels: num_gold_used for {color} barrels {num_gold_used}")
           
    print(f"post_deliver_barrels: list of barrels_delivered {barrels_delivered}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    
    ''' consider duplicating wholesale_catalog to track how much can buy while iterating '''
    plan = []
    print(f"get_wholesale_purchase_plan: wholesale_catalog {wholesale_catalog}")
    with db.engine.begin() as connection:
        num_gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
        print(f"get_wholesale_purchase_plan: num_gold to begin with {num_gold}")
        while num_gold > 0:
            for barrel in wholesale_catalog:
                barrels_to_buy = 1
                if num_gold - barrel.price > 0:
                        barrels_to_buy = num_gold // barrel.price
                        if barrels_to_buy > barrel.quantity:
                            barrels_to_buy = barrel.quantity
                        num_gold = num_gold - (barrels_to_buy * barrel.price)
                        barrel.quantity -= 1
                        print(f"get_wholesale_purchase_plan: before buying num_gold {num_gold}")
                        print(f"get_wholesale_purchase_plan: barrels_to_buy {barrels_to_buy}")
                        plan.append({"sku":barrel.sku, "quantity":barrels_to_buy})

    ''' 
    future plan look at barrel with smallest ml
    buy that, see if that makes ml equal then loop through selling the rest starting at what has the least ml/what we just refilled
    '''
            

    return plan
