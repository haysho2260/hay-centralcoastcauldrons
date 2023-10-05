from fastapi import APIRouter
import sqlalchemy
from src import database as db
from src.api.temp_dict import catalog_dict

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []
    
    # The sql we want to execute
    sql = """
    SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory
    """
    with db.engine.begin() as connection:
        # Run the sql and returns a CursorResult object which represents the SQL results
        # Execute SQL statement to get num of red potions
        result = connection.execute(sqlalchemy.text(sql))
        first_row = result.first()
        if (num_red_potions_to_sell := first_row.num_red_potions) > 0:
            catalog.append({
                    "sku": "RED_POTION",
                    "name": "red potion",
                    "quantity": num_red_potions_to_sell,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                })
            catalog_dict["RED_POTION"] = {
                "sku": "RED_POTION",
                "name": "red potion",
                "quantity": num_red_potions_to_sell,  # Assuming num_red_potions_to_sell is defined elsewhere
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        if (num_green_potions_to_sell := first_row.num_green_potions) > 0:
            catalog.append({
                    "sku": "GREEN_POTION",
                    "name": "green potion",
                    "quantity": num_green_potions_to_sell,
                    "price": 50,
                    "potion_type": [0, 100, 0, 0],
                })
            catalog_dict["GREEN_POTION"] = {
                "sku": "GREEN_POTION",
                "name": "green potion",
                "quantity": num_green_potions_to_sell,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            }
        if (num_blue_potions_to_sell := first_row.num_blue_potions) > 0:
            catalog.append({
                    "sku": "BLUE_POTION_100",
                    "name": "blue potion",
                    "quantity": num_blue_potions_to_sell,
                    "price": 50,
                    "potion_type": [0, 0, 100, 0],
                })
            catalog_dict["BLUE_POTION_100"] = {
                "sku": "BLUE_POTION_100",
                "name": "blue potion",
                "quantity": num_blue_potions_to_sell,
                "price": 50,
                "potion_type": [0, 0, 100, 0],
            }
        print(f"get_catalog: num_red_potions_to_sell {num_red_potions_to_sell}")
        print(f"get_catalog: num_green_potions_to_sell {num_green_potions_to_sell}")
        print(f"get_catalog: num_blue_potions_to_sell {num_blue_potions_to_sell}")

    return catalog
