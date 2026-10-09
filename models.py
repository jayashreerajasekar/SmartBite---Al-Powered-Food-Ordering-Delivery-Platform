"""
models.py
---------
This file contains simple Python functions that read and write data in the
database. Each function does ONE clear job, e.g. get_restaurant_by_id().

We are not using an ORM (like Flask-SQLAlchemy) here. Instead we write plain
SQL inside these functions. This keeps things very easy to explain during a
viva: every function is just "run this SQL, return the result".
"""

from database import get_db
import random
import string
import datetime


# =====================================================================
# USERS
# =====================================================================

def create_user(name, email, phone, password_hash, role="customer"):
    conn = get_db()
    conn.execute(
        "INSERT INTO user (name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        (name, email, phone, password_hash, role),
    )
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM user WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


# =====================================================================
# RESTAURANTS
# =====================================================================

def get_all_restaurants():
    conn = get_db()
    rows = conn.execute("SELECT * FROM restaurant ORDER BY rating DESC").fetchall()
    conn.close()
    return rows


def get_restaurant_by_id(restaurant_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM restaurant WHERE id = ?", (restaurant_id,)).fetchone()
    conn.close()
    return row


def search_restaurants(keyword):
    """Search restaurants by name or cuisine."""
    conn = get_db()
    like = f"%{keyword}%"
    rows = conn.execute(
        "SELECT * FROM restaurant WHERE name LIKE ? OR cuisine LIKE ?",
        (like, like),
    ).fetchall()
    conn.close()
    return rows


def filter_and_sort_restaurants(restaurants, min_rating=None, veg_only=False, sort_by="recommended"):
    """
    Take a list of restaurant rows and apply simple filters/sorting.
    This is plain Python - easy to explain compared to complex SQL.
    """
    result = list(restaurants)

    if min_rating:
        result = [r for r in result if r["rating"] >= float(min_rating)]

    if veg_only:
        result = [r for r in result if r["is_veg_only"] == 1]

    if sort_by == "rating":
        result.sort(key=lambda r: r["rating"], reverse=True)
    elif sort_by == "fastest":
        result.sort(key=lambda r: r["delivery_time"])
    elif sort_by == "price_low":
        result.sort(key=lambda r: r["price_for_two"])
    elif sort_by == "price_high":
        result.sort(key=lambda r: r["price_for_two"], reverse=True)

    return result


# =====================================================================
# FOOD CATEGORIES + FOOD ITEMS
# =====================================================================

def get_all_categories():
    conn = get_db()
    rows = conn.execute("SELECT * FROM food_category ORDER BY name").fetchall()
    conn.close()
    return rows


def get_menu_for_restaurant(restaurant_id):
    """Return every food item that belongs to a restaurant."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM food_item WHERE restaurant_id = ? ORDER BY menu_section, name",
        (restaurant_id,),
    ).fetchall()
    conn.close()
    return rows


def group_menu_by_section(menu_items):
    """Group a flat list of food items into {section_name: [items]}."""
    sections = {}
    for item in menu_items:
        section = item["menu_section"]
        sections.setdefault(section, []).append(item)
    return sections


def get_food_item_by_id(food_item_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM food_item WHERE id = ?", (food_item_id,)).fetchone()
    conn.close()
    return row


def search_food_items(keyword):
    conn = get_db()
    like = f"%{keyword}%"
    rows = conn.execute(
        """SELECT food_item.*, restaurant.name AS restaurant_name
           FROM food_item JOIN restaurant ON food_item.restaurant_id = restaurant.id
           WHERE food_item.name LIKE ? OR food_item.menu_section LIKE ?""",
        (like, like),
    ).fetchall()
    conn.close()
    return rows


# =====================================================================
# CART
# =====================================================================

def get_or_create_cart(user_id, restaurant_id):
    """
    Every user has ONE cart. If they add food from a NEW restaurant,
    we clear the old cart first (like real food-delivery apps do).
    """
    conn = get_db()
    cart = conn.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,)).fetchone()

    if cart is None:
        conn.execute("INSERT INTO cart (user_id, restaurant_id) VALUES (?, ?)", (user_id, restaurant_id))
        conn.commit()
        cart = conn.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,)).fetchone()
    elif cart["restaurant_id"] != restaurant_id:
        # Different restaurant -> empty the old cart items and switch restaurant
        conn.execute("DELETE FROM cart_item WHERE cart_id = ?", (cart["id"],))
        conn.execute("UPDATE cart SET restaurant_id = ? WHERE id = ?", (restaurant_id, cart["id"]))
        conn.commit()
        cart = conn.execute("SELECT * FROM cart WHERE user_id = ?", (user_id,)).fetchone()

    conn.close()
    return cart


def add_item_to_cart(cart_id, food_item_id, quantity, size, extras, extras_price, instructions):
    conn = get_db()
    conn.execute(
        """INSERT INTO cart_item (cart_id, food_item_id, quantity, size, extras, extras_price, special_instructions)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (cart_id, food_item_id, quantity, size, extras, extras_price, instructions),
    )
    conn.commit()
    conn.close()


def get_cart_items(cart_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT cart_item.*, food_item.name, food_item.price, food_item.image, food_item.is_veg
           FROM cart_item JOIN food_item ON cart_item.food_item_id = food_item.id
           WHERE cart_item.cart_id = ?""",
        (cart_id,),
    ).fetchall()
    conn.close()
    return rows


def update_cart_item_quantity(cart_item_id, quantity):
    conn = get_db()
    if quantity <= 0:
        conn.execute("DELETE FROM cart_item WHERE id = ?", (cart_item_id,))
    else:
        conn.execute("UPDATE cart_item SET quantity = ? WHERE id = ?", (quantity, cart_item_id))
    conn.commit()
    conn.close()


def remove_cart_item(cart_item_id):
    conn = get_db()
    conn.execute("DELETE FROM cart_item WHERE id = ?", (cart_item_id,))
    conn.commit()
    conn.close()


def clear_cart(cart_id):
    conn = get_db()
    conn.execute("DELETE FROM cart_item WHERE cart_id = ?", (cart_id,))
    conn.commit()
    conn.close()


def calculate_cart_item_total(cart_item):
    """Price for ONE cart row = (unit price + extras) * quantity."""
    return (cart_item["price"] + cart_item["extras_price"]) * cart_item["quantity"]


def calculate_cart_total(cart_items):
    """Add up every cart row to get the item subtotal."""
    total = 0
    for item in cart_items:
        total += calculate_cart_item_total(item)
    return total


# =====================================================================
# COUPONS  (this is the "calculate_discount" logic the student explains)
# =====================================================================

def get_coupon_by_code(code):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM coupon WHERE code = ? AND is_active = 1", (code.upper(),)
    ).fetchone()
    conn.close()
    return row


def calculate_discount(coupon, order_total):
    """
    Work out how much discount a coupon gives on a given order total.

    Returns a tuple: (discount_amount, error_message)
    If error_message is not empty, the coupon could not be applied.
    """
    if coupon is None:
        return 0, "Invalid coupon code."

    if order_total < coupon["min_order_value"]:
        return 0, f"Minimum order value for this coupon is Rs. {coupon['min_order_value']}."

    if coupon["discount_type"] == "PERCENT":
        discount = int(order_total * coupon["discount_value"] / 100)
        discount = min(discount, coupon["max_discount"])
    else:  # FLAT discount
        discount = coupon["discount_value"]

    # Discount should never be bigger than the order itself
    discount = min(discount, order_total)

    return discount, ""


def get_all_active_coupons():
    conn = get_db()
    rows = conn.execute("SELECT * FROM coupon WHERE is_active = 1").fetchall()
    conn.close()
    return rows


# =====================================================================
# OFFERS
# =====================================================================

def get_all_offers():
    conn = get_db()
    rows = conn.execute("SELECT * FROM offer").fetchall()
    conn.close()
    return rows


# =====================================================================
# ADDRESS
# =====================================================================

def get_addresses_for_user(user_id):
    conn = get_db()
    rows = conn.execute("SELECT * FROM address WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return rows


def get_address_by_id(address_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM address WHERE id = ?", (address_id,)).fetchone()
    conn.close()
    return row


def add_address(user_id, address_type, full_name, phone, house_no, street, area, city, state, pincode, landmark):
    conn = get_db()
    conn.execute(
        """INSERT INTO address (user_id, address_type, full_name, phone, house_no, street, area, city, state, pincode, landmark)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, address_type, full_name, phone, house_no, street, area, city, state, pincode, landmark),
    )
    conn.commit()
    conn.close()


def delete_address(address_id):
    conn = get_db()
    conn.execute("DELETE FROM address WHERE id = ?", (address_id,))
    conn.commit()
    conn.close()


# =====================================================================
# FAVORITES
# =====================================================================

def toggle_favorite_restaurant(user_id, restaurant_id):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM favorite WHERE user_id = ? AND restaurant_id = ?", (user_id, restaurant_id)
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM favorite WHERE id = ?", (existing["id"],))
        is_favorite_now = False
    else:
        conn.execute("INSERT INTO favorite (user_id, restaurant_id) VALUES (?, ?)", (user_id, restaurant_id))
        is_favorite_now = True
    conn.commit()
    conn.close()
    return is_favorite_now


def toggle_favorite_food(user_id, food_item_id):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM favorite WHERE user_id = ? AND food_item_id = ?", (user_id, food_item_id)
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM favorite WHERE id = ?", (existing["id"],))
        is_favorite_now = False
    else:
        conn.execute("INSERT INTO favorite (user_id, food_item_id) VALUES (?, ?)", (user_id, food_item_id))
        is_favorite_now = True
    conn.commit()
    conn.close()
    return is_favorite_now


def get_favorite_restaurants(user_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT restaurant.* FROM favorite JOIN restaurant ON favorite.restaurant_id = restaurant.id
           WHERE favorite.user_id = ?""",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_favorite_foods(user_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT food_item.*, restaurant.name AS restaurant_name FROM favorite
           JOIN food_item ON favorite.food_item_id = food_item.id
           JOIN restaurant ON food_item.restaurant_id = restaurant.id
           WHERE favorite.user_id = ?""",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_favorite_restaurant_ids(user_id):
    conn = get_db()
    rows = conn.execute("SELECT restaurant_id FROM favorite WHERE user_id = ? AND restaurant_id IS NOT NULL", (user_id,)).fetchall()
    conn.close()
    return {row["restaurant_id"] for row in rows}


# =====================================================================
# ORDERS
# =====================================================================

def generate_order_code():
    """Create a readable order code like RIN-ORD-482913."""
    digits = "".join(random.choices(string.digits, k=6))
    return f"RIN-ORD-{digits}"


def generate_transaction_id():
    """Create a readable transaction id like RIN-TXN-482913."""
    digits = "".join(random.choices(string.digits, k=6))
    return f"RIN-TXN-{digits}"


def create_order(user_id, restaurant_id, address_id, item_total, delivery_fee, platform_fee, taxes, discount, coupon_code, grand_total):
    conn = get_db()
    order_code = generate_order_code()
    cur = conn.execute(
        """INSERT INTO "order"
           (order_code, user_id, restaurant_id, address_id, item_total, delivery_fee, platform_fee, taxes, discount, coupon_code, grand_total, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'placed')""",
        (order_code, user_id, restaurant_id, address_id, item_total, delivery_fee, platform_fee, taxes, discount, coupon_code, grand_total),
    )
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id, order_code


def add_order_item(order_id, food_item_id, food_name, quantity, unit_price, size, extras):
    conn = get_db()
    conn.execute(
        """INSERT INTO order_item (order_id, food_item_id, food_name, quantity, unit_price, size, extras)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (order_id, food_item_id, food_name, quantity, unit_price, size, extras),
    )
    conn.commit()
    conn.close()


def get_order_by_id(order_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM "order" WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    return row


def get_orders_for_user(user_id):
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM "order" WHERE user_id = ? ORDER BY created_at DESC', (user_id,)
    ).fetchall()
    conn.close()
    return rows


def get_order_items(order_id):
    conn = get_db()
    rows = conn.execute("SELECT * FROM order_item WHERE order_id = ?", (order_id,)).fetchall()
    conn.close()
    return rows


def update_order_status(order_id, status):
    conn = get_db()
    conn.execute('UPDATE "order" SET status = ? WHERE id = ?', (status, order_id))
    conn.commit()
    conn.close()


def assign_delivery_partner_to_order(order_id, delivery_partner_id):
    conn = get_db()
    conn.execute('UPDATE "order" SET delivery_partner_id = ? WHERE id = ?', (delivery_partner_id, order_id))
    conn.commit()
    conn.close()


def get_all_orders():
    conn = get_db()
    rows = conn.execute('SELECT * FROM "order" ORDER BY created_at DESC').fetchall()
    conn.close()
    return rows


def get_orders_for_delivery_partner(delivery_partner_id):
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM "order" WHERE delivery_partner_id = ? ORDER BY created_at DESC',
        (delivery_partner_id,),
    ).fetchall()
    conn.close()
    return rows


# =====================================================================
# PAYMENT
# =====================================================================

def create_payment(order_id, method, amount, status="success"):
    conn = get_db()
    transaction_id = generate_transaction_id()
    conn.execute(
        "INSERT INTO payment (order_id, transaction_id, method, amount, status) VALUES (?, ?, ?, ?, ?)",
        (order_id, transaction_id, method, amount, status),
    )
    conn.commit()
    conn.close()
    return transaction_id


def get_payment_for_order(order_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM payment WHERE order_id = ?", (order_id,)).fetchone()
    conn.close()
    return row


def get_all_payments():
    conn = get_db()
    rows = conn.execute("SELECT * FROM payment ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


# =====================================================================
# DELIVERY PARTNERS + TRACKING
# =====================================================================

def get_all_delivery_partners():
    conn = get_db()
    rows = conn.execute("SELECT * FROM delivery_partner").fetchall()
    conn.close()
    return rows


def get_delivery_partner_by_id(partner_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM delivery_partner WHERE id = ?", (partner_id,)).fetchone()
    conn.close()
    return row


def pick_random_delivery_partner():
    partners = get_all_delivery_partners()
    return random.choice(partners) if partners else None


def create_tracking_row(order_id, start_lat, start_lng, distance_km, eta_minutes):
    conn = get_db()
    conn.execute(
        """INSERT INTO delivery_tracking (order_id, current_lat, current_lng, distance_remaining_km, eta_minutes, step_index)
           VALUES (?, ?, ?, ?, ?, 0)""",
        (order_id, start_lat, start_lng, distance_km, eta_minutes),
    )
    conn.commit()
    conn.close()


def get_tracking_for_order(order_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM delivery_tracking WHERE order_id = ?", (order_id,)).fetchone()
    conn.close()
    return row


def advance_tracking_step(order_id):
    """
    Move the delivery partner one step closer to the customer.
    This is the simple simulated-GPS logic described in the requirements.
    """
    conn = get_db()
    tracking = conn.execute("SELECT * FROM delivery_tracking WHERE order_id = ?", (order_id,)).fetchone()
    if tracking is None:
        conn.close()
        return None

    order = conn.execute('SELECT * FROM "order" WHERE id = ?', (order_id,)).fetchone()
    restaurant = conn.execute("SELECT * FROM restaurant WHERE id = ?", (order["restaurant_id"],)).fetchone()
    address = conn.execute("SELECT * FROM address WHERE id = ?", (order["address_id"],)).fetchone()

    # A simple fixed customer location a short distance from the restaurant,
    # derived from the address id so every order gets a slightly different spot.
    customer_lat = restaurant["latitude"] + 0.01 + (order["address_id"] or 0) * 0.0008
    customer_lng = restaurant["longitude"] + 0.01 + (order["address_id"] or 0) * 0.0008

    steps = ["placed", "confirmed", "preparing", "ready", "assigned", "picked_up", "out_for_delivery", "delivered"]
    current_index = steps.index(order["status"]) if order["status"] in steps else 0
    next_index = min(current_index + 1, len(steps) - 1)
    next_status = steps[next_index]

    # Move the marker a fraction of the way from restaurant -> customer
    fraction = next_index / (len(steps) - 1)
    new_lat = restaurant["latitude"] + (customer_lat - restaurant["latitude"]) * fraction
    new_lng = restaurant["longitude"] + (customer_lng - restaurant["longitude"]) * fraction

    total_distance = 2.5  # km, matches the requirement's example journey
    remaining_distance = round(total_distance * (1 - fraction), 2)
    eta = max(1, int(15 * (1 - fraction)))

    conn.execute(
        """UPDATE delivery_tracking SET current_lat = ?, current_lng = ?, distance_remaining_km = ?, eta_minutes = ?, step_index = ?
           WHERE order_id = ?""",
        (new_lat, new_lng, remaining_distance, eta, next_index, order_id),
    )
    conn.execute('UPDATE "order" SET status = ? WHERE id = ?', (next_status, order_id))
    conn.commit()
    conn.close()
    return next_status


# =====================================================================
# NOTIFICATIONS
# =====================================================================

STATUS_MESSAGES = {
    "placed": "Your order has been placed.",
    "confirmed": "Your order has been confirmed by the restaurant.",
    "preparing": "Your food is being prepared.",
    "ready": "Your food is ready for pickup.",
    "assigned": "A delivery partner has been assigned to your order.",
    "picked_up": "Your delivery partner has picked up your order.",
    "out_for_delivery": "Your order is out for delivery.",
    "delivered": "Your order has been delivered. Enjoy your meal!",
}


def create_notification(user_id, order_id, message):
    conn = get_db()
    conn.execute(
        "INSERT INTO notification (user_id, order_id, message) VALUES (?, ?, ?)",
        (user_id, order_id, message),
    )
    conn.commit()
    conn.close()


def get_notifications_for_user(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM notification WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (user_id,)
    ).fetchall()
    conn.close()
    return rows


# =====================================================================
# REVIEWS
# =====================================================================

def create_review(user_id, order_id, restaurant_id, restaurant_rating, food_rating, delivery_rating, comment):
    conn = get_db()
    conn.execute(
        """INSERT INTO review (user_id, order_id, restaurant_id, restaurant_rating, food_rating, delivery_rating, comment)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, order_id, restaurant_id, restaurant_rating, food_rating, delivery_rating, comment),
    )
    conn.commit()
    conn.close()


def get_review_for_order(order_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM review WHERE order_id = ?", (order_id,)).fetchone()
    conn.close()
    return row


# =====================================================================
# ADMIN STATISTICS
# =====================================================================

def get_admin_stats():
    conn = get_db()
    stats = {}
    stats["total_users"] = conn.execute("SELECT COUNT(*) AS c FROM user WHERE role = 'customer'").fetchone()["c"]
    stats["total_restaurants"] = conn.execute("SELECT COUNT(*) AS c FROM restaurant").fetchone()["c"]
    stats["total_orders"] = conn.execute('SELECT COUNT(*) AS c FROM "order"').fetchone()["c"]
    stats["total_revenue"] = conn.execute('SELECT COALESCE(SUM(grand_total), 0) AS s FROM "order"').fetchone()["s"]
    stats["active_deliveries"] = conn.execute(
        "SELECT COUNT(*) AS c FROM \"order\" WHERE status IN ('assigned','picked_up','out_for_delivery')"
    ).fetchone()["c"]
    stats["completed_orders"] = conn.execute(
        "SELECT COUNT(*) AS c FROM \"order\" WHERE status = 'delivered'"
    ).fetchone()["c"]
    conn.close()
    return stats
