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
            green_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
        elif barrel_delivered.potion_type == [0,0,1,0]:
            blue_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
        elif barrel_delivered.potion_type == [0,0,0,1]:
            dark_ml += barrel_delivered.ml_per_barrel * barrel_delivered.quantity
        else:
            raise Exception("Invalid potion type")
    print(f"post_deliver_barrels -- gold paid: {gold_paid}; red_ml: {red_ml}; blue_ml: {blue_ml}; green_ml: {green_ml}; dark_ml: {dark_ml} ")
    
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO global_inventory
                (num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold)
                VALUES 
                (:red_ml, :green_ml, :blue_ml, :dark_ml, - :gold_paid)
                """
            ),
            {"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml, "gold_paid": gold_paid}
        )
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    
    ''' consider duplicating wholesale_catalog to track how much can buy while iterating '''
    plan = []
    print(f"get_wholesale_purchase_plan: wholesale_catalog {wholesale_catalog}")
    with db.engine.begin() as connection:
        result_global_inventory = connection.execute(
            sqlalchemy.text("""
                SELECT COALESCE(SUM(gold),0) AS gold, 
                COALESCE(SUM(num_red_ml),0) AS num_red_ml, 
                COALESCE(SUM(num_green_ml),0) AS num_green_ml, 
                COALESCE(SUM(num_blue_ml),0) AS num_blue_ml, 
                COALESCE(SUM(num_dark_ml),0) AS num_dark_ml 
                FROM global_inventory""")
        ).first()

        num_gold = result_global_inventory[0]  # Access the first column (gold)
        red_ml = result_global_inventory[1]     # Access the second column (num_red_ml)
        green_ml = result_global_inventory[2]   # Access the third column (num_green_ml)
        blue_ml = result_global_inventory[3]    # Access the fourth column (num_blue_ml)
        dark_ml = result_global_inventory[4]    # Access the fifth column (num_dark_ml)      
        print(f"get_wholesale_purchase_plan: num_gold to begin with {num_gold}")
        
        
        price_red = -1
        price_green = -1
        quantity_red = 0
        quantity_green = 0
        price_blue = -1
        price_dark = -1
        quantity_blue = 0
        quantity_dark = 0
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_RED_BARREL":
                price_red = barrel.price
                print(f"get_wholesale_purchase_plan: price_red {price_red}")
                quantity_red = barrel.quantity
                print(f"get_wholesale_purchase_plan: quantity_red {quantity_red}")
            elif barrel.sku == "SMALL_GREEN_BARREL":
                price_green = barrel.price
                print(f"get_wholesale_purchase_plan: price_green {price_green}")
                quantity_green = barrel.quantity
                print(f"get_wholesale_purchase_plan: quantity_green {quantity_green}")
            elif barrel.sku == "SMALL_BLUE_BARREL":
                price_blue = barrel.price
                print(f"get_wholesale_purchase_plan: price_blue {price_blue}")
                quantity_blue = barrel.quantity
                print(f"get_wholesale_purchase_plan: quantity_blue {quantity_blue}")
            elif barrel.sku == "SMALL_DARK_BARREL":
                price_dark = barrel.price
                print(f"get_wholesale_purchase_plan: price_dark {price_dark}")
                quantity_dark = barrel.quantity
                print(f"get_wholesale_purchase_plan: quantity_dark {quantity_dark}")
        num_red_barrel = 0
        num_green_barrel = 0
        while num_gold - price_green >= 0 or num_gold - price_red >= 0:
            if red_ml > green_ml and price_green <= num_gold and num_green_barrel < quantity_green:
                num_gold -= price_green
                num_green_barrel += 1
            if red_ml <= green_ml and price_red <= num_gold and num_red_barrel < quantity_red:
                num_gold -= price_red
                num_red_barrel += 1
    print(f"get_wholesale_purchase_plan: after buying num_gold {num_gold}")
            # print(f"get_wholesale_purchase_plan: barrels_to_buy {barrels_to_buy}")
    if num_red_barrel > 0:
        plan.append({
            "sku":"SMALL_RED_BARREL",
            "quantity": num_red_barrel
        })
    if num_green_barrel > 0:
        plan.append({
            "sku":"SMALL_GREEN_BARREL",
            "quantity": num_green_barrel
        })
    return plan
        # plan.append({"sku":barrel.sku, "quantity":barrels_to_buy})

    ''' 
    future plan look at barrel with smallest ml
    buy that, see if that makes ml equal then loop through selling the rest starting at what has the least ml/what we just refilled
    '''
