from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random
from src.api.cart_ids_dict import cart_ids as cart_ids
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
    cart_id = random.randint(0, 2**32 - 1)
    while cart_id in cart_ids:
        cart_id = random.randint(0, 2**32 - 1)
    cart_ids[cart_id] = {"new_cart":new_cart}
    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """returns dictionary definition(?) from cart_ids"""

    return cart_ids[cart_id]


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """If value not in local dict, add to local dict
    if value is in local dict, add quantity to existing value"""
    # cart_ids[cart_id] = {item_sku: cart_item.quantity}
    cart_ids[cart_id]={item_sku:cart_item.quantity}

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
    
    total_potions = 0
    
    with db.engine.begin() as connection:
        cart_data = cart_ids[cart_id]
        print(f"checkout: cart_data {cart_data}")
        print(f"checkout: cart_id {cart_id}")
        for sku, cart_item_data in cart_data.items():
            if sku != "new_cart":
                print(f"checkout: sku {sku}")
                print(f"checkout: sku {sku}")
                if sku == "RED_POTION":
                    quantity_potions_bought = cart_data[sku].quantity
                    print(f"checkout: sku {sku}")
                    if quantity_potions_bought > 0:
                        print(f"checkout: quantity_potions_bought {quantity_potions_bought}")
                        total_potions += quantity_potions_bought
                        print(f"checkout: total_potions {total_potions}")
                        num_red_potions_have = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).first().num_red_potions
                        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {num_red_potions_have - quantity_potions_bought}"))
                        print(f"checkout: num_red_potions_have {num_red_potions_have}")
                        print(f"checkout: sku {sku}")
    
        
        
        
    # TODO: update the gold with total_gold_paid
    return {"total_potions_bought": total_potions, "total_gold_paid": 0}
