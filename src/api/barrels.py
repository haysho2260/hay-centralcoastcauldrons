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
    gold_paid = 0
    red_ml = 0
    blue_ml = 0
    green_ml = 0
    dark_ml = 0
    
    for barrel_delivered in barrels_delivered:
        gold_paid += barrel_delivered.price * barrel_delivered.quantity
        if barrel_delivered.potion_type == [1,0,0,0]:
            red_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
        elif barrel_delivered.potion_type == [0,1,0,0]:
            blue_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
        elif barrel_delivered.potion_type == [0,0,1,0]:
            green_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
        elif barrel_delivered.potion_type == [0,0,0,1]:
            dark_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
        else:
            raise Exception("Invalid potion type")
    print(f"post_deliver_barrels -- gold paid: {gold_paid}; red_ml: {red_ml}; blue_ml: {blue_ml}; green_ml: {green_ml}; dark_ml: {dark_ml} ")
    
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory
                red_ml = red_ml + :red_ml
                green_ml = green_ml + :green_ml
                blue_ml = blue_ml + :blue_ml
                dark_ml = dark_ml + :dark_ml
                gold = gold + :gold_paid
                """
            ),
            [{"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml, "gold_paid": gold_paid}]
        )
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    
    ''' consider duplicating wholesale_catalog to track how much can buy while iterating '''
    plan = []
    print(f"get_wholesale_purchase_plan: wholesale_catalog {wholesale_catalog}")
    with db.engine.begin() as connection:
        result = connection.execute(
            sqlalchemy.text("SELECT gold, red_ml, green_ml, blue_ml, dark_ml FROM global_inventory")
        ).first()
        num_gold, red_ml, green_ml, blue_ml, dark_ml = result        
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
