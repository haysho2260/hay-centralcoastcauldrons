from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    # TODO: reset barrels from inventory, reset carts
    with db.engine.begin() as connection:
        # update
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = 0"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = 0"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = 100"))
    return "OK"


@router.get("/shop_info/")
def get_shop_info():

    return {
        "shop_name": "SHOP HERE!",
        "shop_owner": "Hayley Chang",
    }

