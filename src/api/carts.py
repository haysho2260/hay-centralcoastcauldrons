from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random
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
    # has supabase autogenerate id and return it
    print(f"create_cart: new_cart {new_cart}")
    sql = "INSERT INTO public.cart (cart_id, customer_name) VALUES (DEFAULT, :customer_name)"
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            sql), [{"customer_name": new_cart.customer}])
        cart_id = result.inserted_primary_key[0]
        print(f"create_cart: cart_id {cart_id}")
    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """Retrieve cart item information based on the provided cart_id."""

    result = {}

    sql = sqlalchemy.text(
        """
        SELECT ci.quantity, ci.sku, pc.price
        FROM cart_items AS ci
        JOIN potions_catalog AS pc ON ci.sku = pc.sku
        WHERE ci.cart_id = :cart_id
        """
    ), [{"cart_id": cart_id}]
    try:
        with db.engine.begin() as connection:
            result = connection.execute(sql)
            rows = result.fetchall()

        if rows:
            for row in rows:
                result[row["sku"]] = {
                    "quantity_want": row["quantity"],
                    "price_per": row["price"]
                }
                print(f"get_cart: quantity_want {row['quantity']}")
                print(f"get_cart: sku {row['sku']}")
            return result
    except Exception as e:
        # Handle exceptions, such as database errors
        error_message = f"An error occurred: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """If value not in local dict, add to local dict
    if value is in local dict, add quantity to existing value"""

    try:
        sql = sqlalchemy.text("""
            INSERT INTO public.cart_items 
            (cart_item_id, cart_id, created_at, quantity, sku) 
            VALUES (DEFAULT, :cart_id, DEFAULT, 
            :cart_item.quantity,:item_sku)
        """), [{"cart_id": cart_id, "cart_item.quantity": cart_item.quantity, "item_sku": item_sku}]
        with db.engine.begin() as connection:
            connection.execute(sql)
        return "OK"
    except Exception as e:
        # Handle exceptions, such as database errors
        error_message = f"An error occurred: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    # update gold paid and count num bought
    total_potions_bought = 0
    total_gold_paid = 0

    cart_items = get_cart(cart_id)
    for sku, cart_data in cart_items.items():
        total_gold_paid += cart_data["price_per"]
        total_potions_bought += cart_data["quantity_want"]

    # add gold paid quantities
    sql = sqlalchemy.text(
        """
        -- Update global inventory
        UPDATE global_inventory
        SET gold = gold + :gold_paid;
        """
    ), [{"cart_id": cart_id}]

    with db.engine.begin() as connection:
        connection.execute(sql)
    print(f"checkout: cart_checkout {cart_checkout}")
    print(f"checkout: gold_paid {total_gold_paid}")
    print(f"checkout: total_potions_bought {total_potions_bought}")

    return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
