from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from fastapi import HTTPException
from .catalog import potion_to_sku, sku_to_potion

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
                (:red_ml, :green_ml, :blue_ml, :dark_ml, -:gold_paid)
                """
            ),
            {"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml, "gold_paid": gold_paid}
        )
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    
    ''' consider duplicating wholesale_catalog to track how much can buy while iterating '''

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
        last3_hr_potions = connection.execute(
            sqlalchemy.text("""
                WITH c AS (
                SELECT cart_id
                FROM checkout
                WHERE created_at >= NOW() - INTERVAL '3 hours')
                SELECT ci.sku
                FROM cart_items AS ci
                JOIN c ON c.cart_id = ci.cart_id
                """)
        ).all()
        

        num_gold = result_global_inventory.gold  # Access the first column (gold)
        inventory_ml = [result_global_inventory.num_red_ml, result_global_inventory.num_green_ml, 
                        result_global_inventory.num_blue_ml, result_global_inventory.num_dark_ml]
   
        print(f"get_wholesale_purchase_plan: num_gold to begin with {num_gold}")
        print("num_gold", num_gold, "red_ml:",result_global_inventory.num_red_ml, 
              "green_ml:",result_global_inventory.num_green_ml, "blue_ml:",result_global_inventory.num_blue_ml, 
              "dark_ml:",result_global_inventory.num_dark_ml)
        plan = get_barrel_plan(wholesale_catalog, num_gold, inventory_ml, last3_hr_potions)
        
        
    return plan

    

def get_barrel_plan(wholesale_catalog: list[Barrel], gold, inventory_ml: list[int], last3_hr_potions):
    ''' 
    future plan look at barrel with smallest ml
    buy that, see if that makes ml equal then loop through selling the rest starting at what has the least ml/what we just refilled
    '''
    most_used = [0,0,0,0]
    plan=[]
    for potion in last3_hr_potions:
        p_sku = sku_to_potion(potion.sku)
        most_used[0] += p_sku[1]
        most_used[1] += p_sku[2]
        most_used[2] += p_sku[3]
        most_used[3] += p_sku[4]
    # Sort the barrels by ml per gold spent in ascending order
    wholesale_catalog.sort(key=lambda x: x.ml_per_barrel / x.price)

    # Replenish empty inventory and buy for last 3 hours' potions
    for i in range(4):
        for barrel in wholesale_catalog:
            if inventory_ml[i] == 0 and barrel.potion_type[i] == 1:
                quantity_to_purchase = 1
                if gold - quantity_to_purchase * barrel.price >= 0:
                    plan.append({"sku": barrel.sku, "quantity": quantity_to_purchase})
                    inventory_ml[i] += quantity_to_purchase * barrel.ml_per_barrel
                    gold -= quantity_to_purchase * barrel.price

    # Buy the rest of the barrels efficiently based on ml per gold spent
    for barrel in wholesale_catalog:
        for i in range(4):
            if most_used[i] > 0 and barrel.potion_type[i] == 1:
                quantity_to_purchase = min(barrel.quantity, gold // barrel.price)
                if quantity_to_purchase > 0 and gold - quantity_to_purchase * barrel.price >= 0:
                    plan.append({"sku": barrel.sku, "quantity": quantity_to_purchase})
                    most_used[i] -= quantity_to_purchase * barrel.ml_per_barrel
                    inventory_ml[i] += quantity_to_purchase * barrel.ml_per_barrel
                    gold -= quantity_to_purchase * barrel.price

    return plan





