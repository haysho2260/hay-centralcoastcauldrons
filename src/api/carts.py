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
    sql = """
    INSERT INTO public.cart (cart_id, customer_name) 
    VALUES (DEFAULT, :customer_name)
    RETURNING cart_id
    """
    with db.engine.begin() as connection:
        cart_id = connection.execute(sqlalchemy.text(
            sql), [{"customer_name": new_cart.customer}]).scalar_one()
        print(f"create_cart: cart_id {cart_id}")
    return {"cart_id": cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """Retrieve cart item information based on the provided cart_id. DEPRECATED"""
    raise HTTPException(
        status_code=410, detail="DEPRECATED: ENDPOINT IS NO LONGER AVAILABLE : DUMB FUNCTION")


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """If value not in local dict, add to local dict
    if value is in local dict, add quantity to existing value"""

    try:
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                """
                INSERT INTO public.cart_items 
                (cart_item_id, cart_id, created_at, quantity, sku) 
                VALUES (DEFAULT, :cart_id, DEFAULT, 
                :quantity,:item_sku)
            """),
                [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])
        return "OK"
    except Exception as e:
        # Handle exceptions, such as database errors
        error_message = f"An error occurred: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    try:
        with db.engine.begin() as connection:
            # calculate and return gold paid and num bought
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT 
                        SUM(cart_items.quantity * potions_catalog.price) AS total_gold_paid,
                        SUM(cart_items.quantity) AS total_potions_bought
                    FROM 
                        cart_items
                    JOIN
                        potions_catalog ON cart_items.sku = potions_catalog.sku
                    WHERE 
                        cart_items.cart_id = :cart_id
                    """
                ), {"cart_id": cart_id}).first()
            
            # update current gold available
            connection.execute(sqlalchemy.text("""
                UPDATE global_inventory
                SET gold = gold + :total_gold_paid
                """),
                {"total_gold_paid": result.total_gold_paid}
            )
            # update number of potions in inventory
            connection.execute(sqlalchemy.text("""
                UPDATE potions_catalog AS pc
                SET quantity = pc.quantity - ci.quantity
                FROM cart_items AS ci
                WHERE ci.cart_id = :cart_id
                AND pc.sku = ci.sku;
                """),
                {"cart_id": cart_id}
            )




        print(f"get_cart: total_gold_paid {result.total_gold_paid}")
        print(f"get_cart: total_potions_bought {result.total_potions_bought}")
        return {"total_potions_bought": result.total_potions_bought, "total_gold_paid": result.total_gold_paid}
    except Exception as e:
        # Handle exceptions, such as database errors
        error_message = f"An error occurred: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)

    
