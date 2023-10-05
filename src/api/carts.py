from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random
from src.api.temp_dict import cart_ids, catalog_dict
from fastapi import HTTPException

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str
    


@router.post("/")
def create_cart(new_cart: NewCart):
    """generates a very large number and 
    assigns that to be an id if not in
    cart_ids"""
    print(f"create_cart: new_cart {new_cart}")
    cart_id = random.randint(0, 2**32 - 1)
    while cart_id in cart_ids:
        cart_id = random.randint(0, 2**32 - 1)
    cart_ids[cart_id] = {"new_cart":new_cart}
    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """returns dictionary definition(?) from cart_ids"""

    print(f"get_cart: cart_id{cart_id}")
    return cart_ids[cart_id]


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """If value not in local dict, add to local dict
    if value is in local dict, add quantity to existing value"""
    cart_ids[cart_id]={item_sku:cart_item.quantity}
    print(f"get_cart: cart_id{cart_id}")
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    # update database and deduct number of potions that were bought and incerase
    # Alice makes a post to /carts
    # that returns a cart id in the response
    # then alice makes a post /carts/card_id/items/RED_POTIONS
    # in the body of this post the quanitiy
    if cart_id not in cart_ids:
        # If the cart_id doesn't exist, raise an HTTPException with a 404 status code
        # and the "Cart not found" detail
        raise HTTPException(status_code=404, detail="Cart not found")
    
    total_potions_bought = 0
    total_gold_paid = 0
    
    with db.engine.begin() as connection:
        cart_data = get_cart(cart_id)
        print(f"checkout: cart_data {cart_data}")
        print(f"checkout: cart_id {cart_id}")
        
        
        
        for sku, cart_item_data in cart_data.items():
            if sku != "new_cart": # it can be customer as well
                print(f"checkout: sku {sku}")
                
                # pick which color loop is for
                if "red" in sku.lower():
                    color = "red"
                elif "green" in sku.lower():
                    color = "green"
                elif "blue" in sku.lower():
                    color = "blue"
                else:
                    # consider returning error bc unaccounted for
                    continue
                # get f{color} quantity
                quantity_potions_bought = cart_data[sku].quantity
                print(f"checkout: quantity_potions_bought {quantity_potions_bought}")
                
                # update values if {color} potion was bought
                if quantity_potions_bought > 0:
                    
                    # increment total potions if quantity bought is more than 0
                    total_potions_bought += quantity_potions_bought
                    
                    # check how many potions we have
                    num_potions_have = connection.execute(sqlalchemy.text(f"SELECT num_{color}_potions FROM global_inventory")).scalar()
                    
                    # sell/substract potions
                    connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_{color}_potions = {num_potions_have - quantity_potions_bought}"))
                    print(f"checkout: num_{color}_potions_have {num_potions_have}")

                    # get amount of gold paid for {color} potion and amount gold * quantity bought to total
                    gold_paid += catalog_dict["sku"]["price"] * quantity_potions_bought
                    print(f"checkout: gold_paid for {sku, catalog_dict['sku']['price']}")
        
        # check amount of gold have to increment later
        num_gold_have = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).first().gold
        # increment total gold paid in db
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {num_gold_have + total_gold_paid}"))
        print(f"checkout: gold_paid {total_gold_paid}")
        # print total potions bought but need to increment potions individually because diff colors
        print(f"checkout: total_potions_bought {total_potions_bought}")
    
    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
