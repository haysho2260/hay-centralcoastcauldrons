from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

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
    """Updates in db how many bottles of red potions that we have"""
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_red_potions FROM global_inventory")).first()
        for potion in potions_delivered:
            ''' Update the amount of  num_red_ml'''
            # see how much red ml left
            num_red_ml_have = result.num_red_ml
            # get subtracted amount of red ml
            num_red_ml_subtracted = 100 * potion.quantity
            # update the db with the new num_red_ml
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {num_red_ml_have - num_red_ml_subtracted}"))
            
            '''Update the amount of num_red_potions'''
            # see how much num_red_potions we have
            num_red_potions_have = result.num_red_potions
            # get added amount of num_red_potions
            num_red_potions_added = potion.quantity
            # update the db with the new num_red_potions
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {num_red_potions_have + num_red_potions_added}"))
       
           
    print(potions_delivered)

    return "OK"

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
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
    first_row = result.first()
    num_red_ml = first_row.num_red_ml
    num_potions_bottle = num_red_ml / 100
    
    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": num_potions_bottle,
            }
        ]
