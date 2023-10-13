from fastapi import APIRouter
import sqlalchemy
from src import database as db
import json
router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []

    # Create a SQLAlchemy Table object that represents the "potion_catalog" table
    metadata = sqlalchemy.MetaData()
    potion_catalog = sqlalchemy.Table(
        'potion_catalog', metadata, autoload=True)

    # Create a select statement to retrieve all rows from the "potion_catalog" table
    select_statement = sqlalchemy.select([potion_catalog])

    # Execute the select statement and fetch all rows
    with db.engine.begin() as connection:
        result = connection.execute(select_statement)
        rows = result.fetchall()
        for row in rows:
            
            catalog.append({
                "sku": row.sku,
                "name": row.sku,
                "quantity": row.quantity,
                "price": row.price,
                "potion_type": json.loads(row.sku)
            })
    return catalog
