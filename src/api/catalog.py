from fastapi import APIRouter
import sqlalchemy
from src import database as db
import json
router = APIRouter()


def sku_to_potion(sku):
    parts = sku.split('_')
    return [int(x) for x in parts if x]


def potion_to_sku(potion):
    return '_'.join(map(str, potion))


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []

    # Execute the select statement and fetch all rows
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT pi.sku, pc.price, SUM(pi.quantity) AS sum_quantity
            FROM potions_inventory AS pi
            JOIN potions_catalog AS pc ON pi.sku = pc.sku
            GROUP BY pi.sku, pc.price;
        """))
        rows = result.fetchall()
        for row in rows:
             if row['sum_quantity'] > 0:
                catalog.append({
                    "sku": row['sku'],
                    "name": row['sku'],  # You can adjust 'name' as needed
                    "quantity": row['sum_quantity'],
                    "price": row['price'],
                    "potion_type": sku_to_potion(row['sku'])
                })
    return catalog
