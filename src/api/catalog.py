from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # The sql we want to execute
    sql = """
    SELECT num_red_potions FROM global_inventory
    """
    with db.engine.begin() as connection:
        # Run the sql and returns a CursorResult object which represents the SQL results
        # Execute SQL statement to get num of red potions
        result = connection.execute(sqlalchemy.text(sql))
        first_row = result.first()
        num_red_potions_to_sell = first_row.num_red_potions 
    
    # Can return a max of 20 items.
    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": num_red_potions_to_sell,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            }
        ]
