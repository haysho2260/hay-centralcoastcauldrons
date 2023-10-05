from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from src.api.temp_dict import colors

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
    with db.engine.begin() as connection:
        for color in colors: 
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_{color}_ml = 0"))
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_{color}_potions = 0"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = 100"))
    return "OK"


@router.get("/shop_info/")
def get_shop_info():

    return {
        "shop_name": "SHOP HERE!",
        "shop_owner": "Hayley Chang",
    }

