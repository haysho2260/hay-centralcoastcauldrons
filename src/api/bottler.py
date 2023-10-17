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
                        UPDATE potions_catalog
                        SET quantity = quantity + :quantity
                        WHERE sku = :potion_type;
                        """
                    ),
                    [{"quantity": potion.quantity,
                        "potion_type": potion_to_sku(potion.potion_type)}]
                )
                connection.execute(
                    sqlalchemy.text(
                        """
                        UPDATE global_inventory
                        SET num_red_ml = num_red_ml - :red_ml,
                            num_green_ml = num_green_ml - :green_ml,
                            num_blue_ml = num_blue_ml - :blue_ml,
                            num_dark_ml = num_dark_ml - :dark_ml
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

    plan = []

    with db.engine.begin() as connection:
        colors = connection.execute(sqlalchemy.text(
            "SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory")).first()
        print(f"get_bottle_plan: colors {colors}")
        result = connection.execute(sqlalchemy.text("SELECT sku, quantity FROM potions_catalog")).all()
        for row in result:
            potion_type = sku_to_potion(row.sku)
            quantity_potions = row.quantity
            print(f"get_bottle_plan: potion_type{potion_type}, quantity_potions {quantity_potions}")
            ml_in_potions = []
            for i in range(0, len(potion_type)):
                if potion_type[i] > 0:
                   ml_in_potions.append(colors[i]//potion_type[i]) 
            print(min(potion_type))
            if quantity_potions > 0:
                print(f"get_bottle_plan: potion_type{potion_type}, quantity_bottled {0}")
            else:
                if (potion_type[0] < 100
                    and potion_type[1] < 100
                    and potion_type[2] < 100
                    and potion_type[3] < 100
                    and potion_type[0] <= colors.num_red_ml 
                    and potion_type[1] <= colors.num_green_ml 
                    and potion_type[2] <= colors.num_blue_ml 
                    and potion_type[3] <= colors.num_dark_ml):
                    quantity_bottling = min(potion_type) // 2
                    print(f"get_bottle_plan: potion_type{potion_type}, quantity_bottling {quantity_bottling}")   
                    plan.append({
                        "potion_type": potion_type,
                        "quantity": quantity_bottling
                    })

    return plan
