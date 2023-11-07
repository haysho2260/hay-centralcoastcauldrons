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
        connection.execute(sqlalchemy.text(
            "TRUNCATE cart, cart_items, global_inventory, potions_catalog, potions_inventory, checkout CASCADE"))
        connection.execute(sqlalchemy.text("""
            -- Insert the initial rows
            INSERT INTO public.potions_catalog (sku, price)
            VALUES
                ('50_50_0_0', 65), 
                ('100_0_0_0', 65), 
                ('75_0_0_25', 65), 
                ('0_0_70_30', 70), 
                ('0_0_100_0', 65), 
                ('50_0_50_0', 65), 
                ('75_0_25_0', 65), 
                ('60_40_0_0', 70), 
                ('25_0_75_0', 65), 
                ('70_0_30_0', 70), 
                ('0_0_50_50', 65), 
                ('30_70_0_0', 70), 
                ('0_50_50_0', 65), 
                ('40_0_60_0', 70), 
                ('0_25_75_0', 65), 
                ('0_100_0_0', 65), 
                ('25_75_0_0', 65), 
                ('0_30_70_0', 70), 
                ('25_25_25_25', 65), 
                ('0_75_0_25', 65), 
                ('50_0_0_50', 65), 
                ('0_0_60_40', 70)
        """))
        connection.execute(sqlalchemy.text("""
            -- Insert the initial rows for global
            INSERT INTO public.global_inventory (num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold)
            VALUES (0, 0, 0, 0, 100)

        """))

    return "OK"


@router.get("/shop_info/")
def get_shop_info():

    return {
        "shop_name": "SHOP HERE!",
        "shop_owner": "Hayley Chang",
    }
