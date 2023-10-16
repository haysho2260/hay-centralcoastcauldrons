from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from fastapi import HTTPException
from .catalog import potion_to_sku

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

    result = []

    with db.engine.begin() as connection:
        red, green = connection.execute(sqlalchemy.text(
            "SELECT num_red_ml, num_green_ml FROM global_inventory")).first()
        if red >= 50 and green >= 50:
            result.append({
                "potion_type": [50, 50, 0, 0],
                "quantity": min(red//50, green // 50),
            })
            red -= min(red//50, green // 50)
            green -= min(red//50, green // 50)
        elif red >= 300:
            result.append({
                "potion_type": [100, 0, 0, 0],
                "quantity": 2,
            })
            red -= 2
        elif red < 300 and red > 0:
            result.append({
                "potion_type": [100, 0, 0, 0],
                "quantity": 1,
            })
            red -= 1
        elif green >= 300:
            result.append({
                "potion_type": [0, 100, 0, 0],
                "quantity": 2,
            })
            green -= 2
        elif green < 300 and green > 0:
            result.append({
                "potion_type": [0, 100, 0, 0],
                "quantity": 1,
            })
            green -= 1

    return result
