from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from enum import Enum
from .catalog import potion_to_sku

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"


class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"


@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.
    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.
    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.
    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.
    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    if search_page == "":
        search_page = 0

    sql = """
        SELECT ci.cart_id, c.customer_name, 
        c.created_at, ci.sku, ci.quantity, pc.price
        FROM cart_items as ci
        JOIN cart AS c ON ci.cart_id = c.cart_id
        INNER JOIN potions_catalog AS pc ON ci.sku = pc.sku
        """

    inp = {}

    if customer_name and potion_sku:
        sql += "WHERE c.customer_name ILIKE :customer_name AND ci.sku ILIKE :sku"
        inp = {"customer_name": f"%{customer_name}%", "sku": f"%{potion_sku}%"}
    elif customer_name:
        sql += "WHERE c.customer_name ILIKE :customer_name"
        inp = {"customer_name": f"%{customer_name}%"}
    elif potion_sku:
        sql += "WHERE sku = :sku"
        inp = {"sku": f"%{potion_sku}%"}

    inp["offset"] = search_page  # Replace offset_value with the desired offset

    sort_col_mapping = {
        search_sort_options.customer_name: "c.customer_name",
        search_sort_options.item_sku: "ci.sku",
        search_sort_options.line_item_total: "ci.quantity * pc.price",
        search_sort_options.timestamp: "c.created_at",
    }

    sql += f"""
        ORDER BY {sort_col_mapping[sort_col]}
        {sort_order.value}
        OFFSET :offset LIMIT 6;
    """
    results = []
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql), inp).all()
        for i in range(0, min(5, len(result))):
            cart_id, customer_name, created_at, sku, quantity, price = result[i]
            results.append({
                "line_item_id": cart_id,
                "item_sku": sku,
                "customer_name": customer_name,
                "line_item_total": price * quantity,
                "timestamp": created_at,
            })

    return {
        "previous": str(int(search_page) - 5 if int(search_page) - 5 >= 0 else ""),
        "next": str(int(search_page) + 5 if len(result) >= int(search_page) + 1 else ""),
        "results": results,
    }


class NewCart(BaseModel):
    customer: str

# no unit test for create cart


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
        connection.execute(sqlalchemy.text(
            """
            INSERT INTO public.checkout (cart_id) 
            VALUES (:cart_id)
            """
        ), {"cart_id": cart_id})
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
                [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": potion_to_sku(item_sku.split(','))}])
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
            # check if checked out previously
            recent_checked_out = connection.execute(sqlalchemy.text("""
                SELECT checked_out
                FROM checkout
                WHERE cart_id = :cart_id
                ORDER BY created_at DESC
                LIMIT 1
            """), {"cart_id": cart_id}).scalar()
            if recent_checked_out:
                # If already checked out, return an error
                raise HTTPException(
                    status_code=400, detail="This item has already been checked out.")

            # mark as checked out if not
            connection.execute(sqlalchemy.text("""
                INSERT INTO checkout (cart_id, checked_out)
                VALUES (:cart_id, TRUE)
                """), {"cart_id": cart_id})
            # calculate and return gold paid and num bought
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT 
                        COALESCE(SUM(cart_items.quantity * potions_catalog.price),0) AS total_gold_paid,
                        COALESCE(SUM(cart_items.quantity),0) AS total_potions_bought
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
                INSERT INTO global_inventory (gold)
                VALUES (:total_gold_paid);
            """), {"total_gold_paid": result.total_gold_paid})
            # update number of potions in inventory
            connection.execute(sqlalchemy.text("""
                INSERT INTO potions_inventory (quantity, sku)
                SELECT -ci.quantity, ci.sku
                FROM cart_items AS ci
                WHERE ci.cart_id = :cart_id;
                """),
                               {"cart_id": cart_id}
                               )

            print(f"get_cart: total_gold_paid {result.total_gold_paid}")
            print(
                f"get_cart: total_potions_bought {result.total_potions_bought}")
            return {"total_potions_bought": result.total_potions_bought, "total_gold_paid": result.total_gold_paid}
    except IntegrityError as e:
        # Handle exceptions, such as database errors
        error_message = f"An error occurred: {str(e)}"
        raise HTTPException(status_code=500, detail=error_message)
