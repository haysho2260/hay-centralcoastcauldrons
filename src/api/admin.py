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
    with db.engine.begin() as connection:
        # Drop existing tables
        connection.execute("DROP TABLE IF EXISTS cart, cart_items, global_inventory, potions_catalog CASCADE")

        # Recreate tables based on schema.sql
        with open("../../schema.sql", "r") as schema_file:
            schema_sql = schema_file.read()
            connection.execute(schema_sql)
    return "OK"


@router.get("/shop_info/")
def get_shop_info():

    return {
        "shop_name": "SHOP HERE!",
        "shop_owner": "Hayley Chang",
    }

