from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from src.api.temp_dict import colors
from fastapi import HTTPException

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """Updates in db how many bottles of red potions that we have"""
    
    print(f"post_deliver_bottles: potions_delivered {potions_delivered}")
    # how do i know what potion ml I use
        # in potion type first int is red_ml
    with db.engine.begin() as connection:
        for color in colors:
            # Define the SQL query with placeholders for color
            sql = """
                SELECT num_{}_ml, num_{}_potions FROM global_inventory
            """

            # Replace the placeholders with the actual color value
            formatted_sql = sql.format(color, color)

            # Execute the query
            # see how much num_ml & num_potions we have
            num_ml_have, num_potions_have = connection.execute(sqlalchemy.text(formatted_sql)).first()
            
            for potion in potions_delivered:
                ''' Update the amount of  num_red_ml'''
                # see how much red ml left
                # get subtracted amount of red ml
                num_ml_subtracted = 100 * potion.quantity
                # update the db with the new num_red_ml
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_{color}_ml = {num_ml_have - num_ml_subtracted}"))
                print(f"potion num_{color}_ml_have {num_ml_have}")
                print(f"potion num_{color}_ml_subtracted {num_ml_subtracted}")
                
                '''Update the amount of num_red_potions'''
                # get added amount of num_red_potions
                num_potions_added = potion.quantity
                # update the db with the new num_red_potions
                
                print(f"post_deliver_bottles: num_{color}_potions_have {num_potions_have}")
                print(f"num_red_potions_added: num_{color}_potions_added {num_potions_added}")
                
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {num_potions_have + num_potions_added}"))
       
           
    print(potions_delivered)

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, gree, and blue potions to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    
    
    
    result = []
    

    with db.engine.begin() as connection:
        for color in colors:
            num_ml = connection.execute(sqlalchemy.text(f"SELECT num_{color}_ml FROM global_inventory")).scalar()
            num_potions_bottle = num_ml // 100
            if color == "red":
                potion_type = [100, 0, 0, 0]
            elif color == "green":
                potion_type = [0, 100, 0, 0]
            elif color == "blue":
                potion_type = [0, 0, 100, 0]
            else:
                raise HTTPException(status_code=500, detail="Bug in looping through colors")
            result.append({
                "potion_type": potion_type,
                "quantity": num_potions_bottle,
            })
    
        print(f"num{color}_ml {num_ml}")
        print(f"num_{color}_potions_bottle {num_potions_bottle}")
    
    return result
