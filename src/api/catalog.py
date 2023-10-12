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
                "name": row.name,
                "quantity": row.quantity,
                "price": row.price,
                "potion_type": [row.red, row.green, row.blue, row.dark],
            })
    return catalog
