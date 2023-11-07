from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from fastapi import HTTPException
from .catalog import potion_to_sku, sku_to_potion

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)


class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int


@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    print(f"post_deliver_bottles: potions_delivered {potions_delivered}")
    """Updates in db how many bottles of potions that we have"""
    # subtract quantities
    try:
        for potion in potions_delivered:
            # Update potion catalog
            with db.engine.begin() as connection:
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO potions_inventory
                        (quantity, sku)
                        VALUES (:quantity, :sku)
                        """
                    ),
                    [{"quantity": potion.quantity,
                        "sku": potion_to_sku(potion.potion_type)}]
                )
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO global_inventory (num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold)
                        VALUES (-:red_ml, -:green_ml, -:blue_ml, -:dark_ml, 0)
                        """
                    ),
                    [{"red_ml": potion.potion_type[0] * potion.quantity, "green_ml": potion.potion_type[1] * potion.quantity,
                        "blue_ml": potion.potion_type[2] * potion.quantity, "dark_ml": potion.potion_type[3] * potion.quantity}]
                )
        print(potions_delivered)

        return "OK"
    except Exception as e:
        # Handle exceptions, such as database errors
        error_message = f"An error occurred: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)

# Gets called 4 times a day


@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, gree, and blue potions to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    

    with db.engine.begin() as connection:
        colors = connection.execute(sqlalchemy.text(
            """SELECT COALESCE(SUM(num_red_ml),0) AS num_red_ml, 
            COALESCE(SUM(num_green_ml),0) AS num_green_ml, 
            COALESCE(SUM(num_blue_ml),0) AS num_blue_ml, 
            COALESCE(SUM(num_dark_ml),0) AS num_dark_ml
            FROM global_inventory""")).first()
        print(f"get_bottle_plan: colors {colors}")
        potions_in_inventory = connection.execute(sqlalchemy.text("""
            SELECT pc.sku, COALESCE(SUM(pi.quantity), 0) AS sum_quantity
            FROM potions_catalog pc
            LEFT JOIN potions_inventory pi ON pc.sku = pi.sku
            GROUP BY pc.sku
            ORDER BY sum_quantity ASC;
        """)).all()
        last3_hr_potions = connection.execute(
            sqlalchemy.text("""
                WITH c AS (
                    SELECT cart_id
                    FROM checkout
                    WHERE created_at >= NOW() - INTERVAL '3 hours'
                )
                SELECT ci.sku, COUNT(ci.sku) AS sku_count
                FROM cart_items AS ci
                JOIN c ON c.cart_id = ci.cart_id
                GROUP BY ci.sku
                """)
        ).all()

        
        inventory_ml = [colors.num_red_ml, colors.num_green_ml, colors.num_blue_ml, colors.num_dark_ml]
        plan=mix_potions(inventory_ml, potions_in_inventory, last3_hr_potions)
        

    return plan

def mix_potions(inventory_ml, potions_in_inventory, last3_hr_potions):
    inventory_potions = {potion.sku: potion.sum_quantity for potion in potions_in_inventory}
    last3_hr_potions_dict = {potion.sku: potion.sku_count for potion in last3_hr_potions}
    plan = []

    # Replenish recently bought potions to have 1/3 of their original quantity
    for sku, quantity in inventory_potions.items():
        if sku in last3_hr_potions_dict and last3_hr_potions_dict[sku] > 0:
            potion_type = sku_to_potion(sku)
            replenish_quantity = (quantity * 2/3) // 1
            ml_needed = [potion_type[i] * replenish_quantity for i in range(4)]

            # Check if you have enough ml in inventory to make these potions
            if all(ml_needed[i] <= inventory_ml[i] for i in range(4)):
                plan.append({
                    "potion_type": potion_type,
                    "quantity": replenish_quantity
                })
                # Deduct the used ml from inventory
                for i in range(4):
                    inventory_ml[i] -= ml_needed[i]

    # Replenish potions with 0 quantity
    for sku, quantity in inventory_potions.items():
        if quantity == 0:
            potion_type = sku_to_potion(sku)
            replenish_quantity = 1
            ml_needed = [potion_type[i] * replenish_quantity for i in range(4)]

            # Check if you have enough ml in inventory to make these potions
            if all(ml_needed[i] <= inventory_ml[i] for i in range(4)):
                plan.append({
                    "potion_type": potion_type,
                    "quantity": replenish_quantity
                })
                # Deduct the used ml from inventory
                for i in range(4):
                    inventory_ml[i] -= ml_needed[i]

    return plan

