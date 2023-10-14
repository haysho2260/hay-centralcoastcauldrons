from fastapi import APIRouter
import sqlalchemy
from src import database as db
import json
router = APIRouter()


def sku_to_potion(sku):
    return [int(x) for x in sku[1:-1].split('_')]


def potion_to_sku(potion):
    return f"[{'_'.join(map(str, potion))}]"


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []

    # Execute the select statement and fetch all rows
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT sku, quantity, price FROM potions_catalog"))
        rows = result.fetchall()
        for row in rows:
 
            catalog.append({
                "sku": row.sku,
                "name": row.sku,
                "quantity": row.quantity,
                "price": row.price,
                "potion_type": sku_to_potion(row.sku)
            })
    return catalog
