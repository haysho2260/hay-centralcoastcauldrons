from fastapi import APIRouter
import sqlalchemy
from src import database as db
import json
router = APIRouter()
import random


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
    

    # Execute the select statement and fetch all rows
    with db.engine.begin() as connection:
        potions_in_inventory = connection.execute(sqlalchemy.text("""
            SELECT pi.sku, COALESCE(SUM(pi.quantity),0) AS quantity, SUM(pc.price) AS price
            FROM potions_inventory AS pi
            LEFT JOIN potions_catalog AS pc ON pi.sku = pc.sku
            GROUP BY pi.sku
            HAVING SUM(pi.quantity) > 0;
            
            WITH potion_price AS (
            SELECT SUM(pc.price) AS price, pc.sku
            FROM potions_catalog AS pc
            GROUP BY pc.sku
            ),
            potion_quantity AS (
              SELECT pi.sku, SUM(pi.quantity) AS quantity
              FROM potions_inventory AS pi
              GROUP BY pi.sku
            )
            SELECT potion_price.price AS price, potion_quantity.sku AS sku, potion_quantity.quantity AS quantity
            FROM potion_price
            JOIN potion_quantity ON potion_quantity.sku = potion_price.sku
        """)).all()
        last3_hr_potions = connection.execute(
            sqlalchemy.text("""
                WITH c AS (
                    SELECT cart_id
                    FROM checkout
                    WHERE created_at >= NOW() - INTERVAL '3 hours'
                )
                SELECT ci.sku AS sku, COUNT(ci.sku) AS quantity, SUM(pc.price) AS price
                FROM cart_items AS ci
                JOIN c ON c.cart_id = ci.cart_id
                LEFT JOIN potions_catalog AS pc ON ci.sku = pc.sku
                GROUP BY ci.sku
                ORDER BY COUNT(ci.sku) DESC;
            """)
        ).all() 
        prices_updated = connection.execute(sqlalchemy.text("""
           SELECT CASE
            WHEN MAX(created_at) >= NOW() - INTERVAL '3 hours' THEN true
            ELSE false
            END AS last_change_within_last_hour
            FROM potions_catalog;
            """)
        ).scalar()
        if not prices_updated:
            adjust_potion_prices(potions_in_inventory, last3_hr_potions)
        catalog = limit_catalog(potions_in_inventory, last3_hr_potions)
        
    return catalog

def limit_catalog(potions_in_inventory, last3_hr_potions):
    # order the most recently sold by price
    # add all to catalog
    # limit to 6
    # if more room, randomly select anything in inventory where quantity > 0 
    catalog = []
    for potion in last3_hr_potions:
        print(potion)
        if potion.quantity > 0:
            catalog.append({
                "sku": potion.sku,
                "name": potion.sku,  # You can adjust 'name' as needed
                "quantity": potion.quantity,
                "price": potion.price,
                "potion_type": sku_to_potion(potion.sku)
            })
    if len(last3_hr_potions) < 6:
        # Create a list of SKUs in last3_hr_potions
        last3_hr_sku_set = set(potion.sku for potion in last3_hr_potions)
        
        # Filter inventory potions by quantity > 0 and not in last3_hr_potions
        eligible_potions = [potion for potion in potions_in_inventory if potion.quantity > 0 and potion.sku not in last3_hr_sku_set]
        
        # Shuffle the eligible potions and add up to (6 - len(catalog)) of them
        random.shuffle(eligible_potions)
        additional_potions = eligible_potions[:6 - len(catalog)]
        
        # Add the selected additional potions to the catalog
        for potion in additional_potions:
            catalog.append({
                "sku": potion.sku,
                "name": potion.sku,  # You can adjust 'name' as needed
                "quantity": potion.quantity,
                "price": potion.price,
                "potion_type": sku_to_potion(potion.sku)
            })
    return catalog
def adjust_potion_prices(potions_in_inventory, last3_hr_potions):
    '''increment prices if doing well and decrement otherwise'''
    inventory_potions = {potion.sku: potion.quantity for potion in potions_in_inventory}
    last3_hr_potions_dict = {potion.sku: potion.sku_count for potion in last3_hr_potions}

    for potion in inventory_potions:
        if potion.sku in last3_hr_potions_dict:
            if potion.price < 500:
                with db.engine.begin() as connection:
                    connection.execute(sqlalchemy.text(
                    """
                        INSERT INTO public.potions_catalog 
                        (sku, price) 
                        VALUES (:sku,  
                        :price)
                    """),
                        [{"sku": potion.sku, "price": 5}])
            else:
                with db.engine.begin() as connection:
                    connection.execute(sqlalchemy.text(
                    """
                        INSERT INTO public.potions_catalog 
                        (sku, price) 
                        VALUES (:sku,  
                        :price)
                    """),
                        [{"sku": potion.sku, "price": 500-potion.price}])
        else:
            if last3_hr_potions_dict[potion.sku].price > 25:
                with db.engine.begin() as connection:
                    connection.execute(sqlalchemy.text(
                    """
                        INSERT INTO public.potions_catalog 
                        (sku, price) 
                        VALUES (:sku,  
                        :price)
                    """),
                        [{"sku": potion.sku, "price": -5}])
    return "OK"