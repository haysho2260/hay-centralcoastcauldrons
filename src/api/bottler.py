from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from fastapi import HTTPException

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
    """Updates in db how many bottles of potions that we have"""
    # subtract quantities
    try:
        for potion in potions_delivered:
            sql = sqlalchemy.text(
                """
                -- Update potion catalog
                UPDATE potion_catalog
                SET quantity = quantity - :quantity
                WHERE potion_type = :potion_type;
                """
            )[{"quantity": potion.quantity, "potion_type": str(potion.potion_type)}]

            with db.engine.begin() as connection:
                connection.execute(sql)
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
        else:
            raise HTTPException(
                status_code=500, detail="Bug in looping through colors")

    return result
