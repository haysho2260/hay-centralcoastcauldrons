from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random
from src.api.cart_ids_dict import cart_ids as cart_ids

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
    cart_ids[cart_id] = {"cart":new_cart}
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
    if item_sku in cart_ids[cart_id]:
        cart_ids[cart_id][item_sku]["cart_item"] += cart_item
    else:
        cart_ids[cart_id]["sku"] = item_sku
        cart_ids[cart_id][item_sku]["cart_item"] = cart_item

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
    total_potions = 0
    print(f"cart checkout payment {cart_checkout.payment}")
    for sku in cart_ids[cart_id]:
        quantity_potions_bought = sku["cart_item"].quantity
        total_potions += quantity_potions_bought
    return {"total_potions_bought": total_potions, "total_gold_paid": 0}
