"""
app.py
------
This is the main file of RIN'S SMART BITE. It creates the Flask application
and defines every route (URL) in the website.

HOW LOGIN WORKS (for the viva):
  - We do NOT use the Flask-Login extension. Instead we use Flask's built-in
    "session" object, which stores a small encrypted cookie in the user's
    browser containing their user id and role.
  - When someone logs in successfully, we save session["user_id"] and
    session["role"].
  - The login_required() decorator checks whether session["user_id"] exists
    before allowing access to a page.
  - Passwords are never stored as plain text - werkzeug's generate_password_hash
    and check_password_hash take care of secure hashing.

HOW THE CART WORKS:
  - Every logged-in user has one Cart row. Adding food creates a CartItem.
  - functions in models.py do the actual database work; the routes here
    just call those functions and pass data to the HTML templates.

HOW COUPONS WORK:
  - models.calculate_discount() takes a Coupon row and an order total and
    returns how much discount applies. See that function for the full logic.

HOW PAYMENT WORKS:
  - This is a DEMO payment flow only - no real money is involved.
  - We simply generate a fake transaction id (RIN-TXN-XXXXXX) and store it.

HOW AN ORDER IS CREATED:
  - checkout() collects the address + coupon, payment() finalises the order,
    creates OrderItem rows from the cart, clears the cart, creates a Payment
    row, and randomly assigns a DeliveryPartner + starting DeliveryTracking row.

HOW TRACKING WORKS:
  - Each order has one DeliveryTracking row storing the delivery partner's
    current simulated GPS coordinates. A JavaScript timer on the tracking
    page calls /api/advance_order/<id> every few seconds, and each call moves
    the order one step forward (see models.advance_tracking_step).

HOW THE MAP WORKS:
  - The tracking page embeds a Leaflet map (JavaScript library) showing three
    markers: restaurant, delivery partner, customer. Python only supplies the
    latitude/longitude numbers - the animation itself is simple JavaScript.
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

import models
from database import DB_PATH
import os

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "local-development-only-change-before-deploy"
)


# =====================================================================
# HELPER: login_required decorator
# =====================================================================

def login_required(role=None):
    """
    A decorator factory. Usage:
        @login_required()               -> any logged in user
        @login_required(role="admin")   -> only admins
        @login_required(role="delivery")-> only delivery partners
    """
    def decorator(view_function):
        @wraps(view_function)
        def wrapped_view(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.")
                return redirect(url_for("login"))
            if role is not None and session.get("role") != role:
                flash("You do not have permission to view that page.")
                return redirect(url_for("index"))
            return view_function(*args, **kwargs)
        return wrapped_view
    return decorator


def current_user():
    if "user_id" not in session:
        return None
    return models.get_user_by_id(session["user_id"])


@app.context_processor
def inject_globals():
    """Make some variables available to EVERY template automatically."""
    user = current_user()
    cart_count = 0
    if user:
        # Only count items if a cart already exists (avoid creating empty carts on every page)
        conn = models.get_db()
        cart_row = conn.execute("SELECT id FROM cart WHERE user_id = ?", (user["id"],)).fetchone()
        if cart_row:
            count_row = conn.execute(
                "SELECT COALESCE(SUM(quantity), 0) AS c FROM cart_item WHERE cart_id = ?", (cart_row["id"],)
            ).fetchone()
            cart_count = count_row["c"]
        conn.close()
    return dict(current_user=user, cart_count=cart_count, app_name="RIN'S SMART BITE")


# =====================================================================
# HOME PAGE
# =====================================================================

@app.route("/")
def index():
    restaurants = models.get_all_restaurants()
    categories = models.get_all_categories()
    offers = models.get_all_offers()[:6]
    favorite_ids = models.get_favorite_restaurant_ids(session["user_id"]) if "user_id" in session else set()
    return render_template(
        "index.html",
        restaurants=restaurants[:12],
        categories=categories,
        offers=offers,
        favorite_ids=favorite_ids,
    )


# =====================================================================
# AUTHENTICATION
# =====================================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form["password"]

        if models.get_user_by_email(email):
            flash("An account with that email already exists. Please log in.")
            return redirect(url_for("login"))

        password_hash = generate_password_hash(password)
        models.create_user(name, email, phone, password_hash, role="customer")
        flash("Account created successfully! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = models.get_user_by_email(email)

        # check_password_hash compares the entered password against the
        # securely hashed password stored in the database.
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["name"] = user["name"]

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        elif user["role"] == "delivery":
            return redirect(url_for("delivery_dashboard"))
        else:
            return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# =====================================================================
# RESTAURANTS
# =====================================================================

@app.route("/restaurants")
def restaurants_page():
    keyword = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sort_by = request.args.get("sort", "recommended")
    min_rating = request.args.get("min_rating")
    veg_only = request.args.get("veg_only") == "1"

    if keyword:
        restaurants = models.search_restaurants(keyword)
    elif category:
        restaurants = models.search_restaurants(category)
    else:
        restaurants = models.get_all_restaurants()

    restaurants = models.filter_and_sort_restaurants(
        restaurants, min_rating=min_rating, veg_only=veg_only, sort_by=sort_by
    )

    food_matches = models.search_food_items(keyword) if keyword else []
    favorite_ids = models.get_favorite_restaurant_ids(session["user_id"]) if "user_id" in session else set()

    return render_template(
        "restaurants.html",
        restaurants=restaurants,
        keyword=keyword,
        category=category,
        sort_by=sort_by,
        food_matches=food_matches,
        favorite_ids=favorite_ids,
    )


@app.route("/restaurant/<int:restaurant_id>")
def restaurant_page(restaurant_id):
    restaurant = models.get_restaurant_by_id(restaurant_id)
    if restaurant is None:
        flash("Restaurant not found.")
        return redirect(url_for("restaurants_page"))

    menu_items = models.get_menu_for_restaurant(restaurant_id)
    sections = models.group_menu_by_section(menu_items)

    favorite_ids = models.get_favorite_restaurant_ids(session["user_id"]) if "user_id" in session else set()
    is_favorite = restaurant_id in favorite_ids

    return render_template(
        "restaurant.html",
        restaurant=restaurant,
        sections=sections,
        is_favorite=is_favorite,
        extras_pool=[("Extra Cheese", 40), ("Extra Chicken", 80), ("Extra Sauce", 20)],
    )


@app.route("/favorite/restaurant/<int:restaurant_id>", methods=["POST"])
@login_required()
def favorite_restaurant(restaurant_id):
    is_fav = models.toggle_favorite_restaurant(session["user_id"], restaurant_id)
    return jsonify({"is_favorite": is_fav})


@app.route("/favorite/food/<int:food_item_id>", methods=["POST"])
@login_required()
def favorite_food(food_item_id):
    is_fav = models.toggle_favorite_food(session["user_id"], food_item_id)
    return jsonify({"is_favorite": is_fav})


# =====================================================================
# OFFERS PAGE
# =====================================================================

@app.route("/offers")
def offers_page():
    offers = models.get_all_offers()
    coupons = models.get_all_active_coupons()
    return render_template("offers.html", offers=offers, coupons=coupons)


# =====================================================================
# CART
# =====================================================================

@app.route("/cart/add/<int:food_item_id>", methods=["POST"])
@login_required()
def add_to_cart(food_item_id):
    food_item = models.get_food_item_by_id(food_item_id)
    if food_item is None:
        flash("Food item not found.")
        return redirect(url_for("index"))

    quantity = int(request.form.get("quantity", 1))
    size = request.form.get("size", "Regular")
    selected_extras = request.form.getlist("extras")
    instructions = request.form.get("instructions", "")

    # Work out the total extra price using the shared EXTRAS price list
    extras_price_map = {"Extra Cheese": 40, "Extra Chicken": 80, "Extra Sauce": 20}
    extras_price = sum(extras_price_map.get(name, 0) for name in selected_extras)
    extras_text = ", ".join(selected_extras)

    cart = models.get_or_create_cart(session["user_id"], food_item["restaurant_id"])
    models.add_item_to_cart(cart["id"], food_item_id, quantity, size, extras_text, extras_price, instructions)

    flash(f"{food_item['name']} added to cart!")
    return redirect(request.referrer or url_for("index"))


@app.route("/cart")
@login_required()
def cart_page():
    conn = models.get_db()
    cart = conn.execute("SELECT * FROM cart WHERE user_id = ?", (session["user_id"],)).fetchone()
    conn.close()

    if cart is None:
        return render_template("cart.html", cart_items=[], restaurant=None, totals=None)

    cart_items = models.get_cart_items(cart["id"])
    restaurant = models.get_restaurant_by_id(cart["restaurant_id"])

    item_total = models.calculate_cart_total(cart_items)
    delivery_fee = restaurant["delivery_fee"] if restaurant else 0
    platform_fee = 5 if item_total > 0 else 0
    taxes = int(item_total * 0.05)  # simple 5% tax for the demo
    grand_total = item_total + delivery_fee + platform_fee + taxes

    applied_code = session.get("applied_coupon")
    discount = 0
    coupon_error = ""
    if applied_code:
        coupon = models.get_coupon_by_code(applied_code)
        discount, coupon_error = models.calculate_discount(coupon, item_total)
        if coupon_error:
            session.pop("applied_coupon", None)
            discount = 0

    grand_total = max(0, grand_total - discount)

    totals = {
        "item_total": item_total,
        "delivery_fee": delivery_fee,
        "platform_fee": platform_fee,
        "taxes": taxes,
        "discount": discount,
        "grand_total": grand_total,
        "coupon_code": applied_code if discount > 0 else None,
    }

    return render_template("cart.html", cart_items=cart_items, restaurant=restaurant, totals=totals)


@app.route("/cart/update/<int:cart_item_id>", methods=["POST"])
@login_required()
def update_cart_item(cart_item_id):
    action = request.form.get("action")
    conn = models.get_db()
    row = conn.execute("SELECT * FROM cart_item WHERE id = ?", (cart_item_id,)).fetchone()
    conn.close()
    if row is None:
        return redirect(url_for("cart_page"))

    new_quantity = row["quantity"] + 1 if action == "increase" else row["quantity"] - 1
    models.update_cart_item_quantity(cart_item_id, new_quantity)
    return redirect(url_for("cart_page"))


@app.route("/cart/remove/<int:cart_item_id>", methods=["POST"])
@login_required()
def remove_cart_item(cart_item_id):
    models.remove_cart_item(cart_item_id)
    return redirect(url_for("cart_page"))


@app.route("/cart/apply_coupon", methods=["POST"])
@login_required()
def apply_coupon():
    code = request.form.get("code", "").strip().upper()
    coupon = models.get_coupon_by_code(code)

    conn = models.get_db()
    cart = conn.execute("SELECT * FROM cart WHERE user_id = ?", (session["user_id"],)).fetchone()
    conn.close()

    item_total = 0
    if cart:
        cart_items = models.get_cart_items(cart["id"])
        item_total = models.calculate_cart_total(cart_items)

    discount, error = models.calculate_discount(coupon, item_total)
    if error:
        flash(error)
    else:
        session["applied_coupon"] = code
        flash(f"Coupon {code} applied! You saved Rs.{discount}.")

    return redirect(url_for("cart_page"))


@app.route("/cart/remove_coupon", methods=["POST"])
@login_required()
def remove_coupon():
    session.pop("applied_coupon", None)
    return redirect(url_for("cart_page"))


# =====================================================================
# CHECKOUT + ADDRESS
# =====================================================================

@app.route("/checkout")
@login_required()
def checkout():
    addresses = models.get_addresses_for_user(session["user_id"])
    conn = models.get_db()
    cart = conn.execute("SELECT * FROM cart WHERE user_id = ?", (session["user_id"],)).fetchone()
    conn.close()

    if cart is None:
        flash("Your cart is empty.")
        return redirect(url_for("cart_page"))

    cart_items = models.get_cart_items(cart["id"])
    if not cart_items:
        flash("Your cart is empty.")
        return redirect(url_for("cart_page"))

    return render_template("checkout.html", addresses=addresses)


@app.route("/address/add", methods=["POST"])
@login_required()
def add_address():
    models.add_address(
        session["user_id"],
        request.form.get("address_type", "HOME"),
        request.form.get("full_name"),
        request.form.get("phone"),
        request.form.get("house_no"),
        request.form.get("street"),
        request.form.get("area"),
        request.form.get("city"),
        request.form.get("state"),
        request.form.get("pincode"),
        request.form.get("landmark"),
    )
    flash("Address added.")
    return redirect(url_for("checkout"))


@app.route("/address/delete/<int:address_id>", methods=["POST"])
@login_required()
def delete_address(address_id):
    models.delete_address(address_id)
    flash("Address removed.")
    return redirect(url_for("checkout"))


# =====================================================================
# PAYMENT (demo only - no real money involved)
# =====================================================================

@app.route("/payment", methods=["GET", "POST"])
@login_required()
def payment_page():
    if request.method == "GET":
        address_id = request.args.get("address_id")
        if not address_id:
            flash("Please select a delivery address.")
            return redirect(url_for("checkout"))
        return render_template("payment.html", address_id=address_id)

    # POST: process the demo payment and create the order
    address_id = request.form.get("address_id")
    method = request.form.get("method", "COD")

    conn = models.get_db()
    cart = conn.execute("SELECT * FROM cart WHERE user_id = ?", (session["user_id"],)).fetchone()
    conn.close()

    if cart is None:
        flash("Your cart is empty.")
        return redirect(url_for("cart_page"))

    cart_items = models.get_cart_items(cart["id"])
    if not cart_items:
        flash("Your cart is empty.")
        return redirect(url_for("cart_page"))

    restaurant = models.get_restaurant_by_id(cart["restaurant_id"])

    # ---- Recalculate the final price on the server (never trust the client) ----
    item_total = models.calculate_cart_total(cart_items)
    delivery_fee = restaurant["delivery_fee"]
    platform_fee = 5
    taxes = int(item_total * 0.05)

    applied_code = session.get("applied_coupon")
    discount = 0
    if applied_code:
        coupon = models.get_coupon_by_code(applied_code)
        discount, _ = models.calculate_discount(coupon, item_total)

    grand_total = max(0, item_total + delivery_fee + platform_fee + taxes - discount)

    # ---- Create the order ----
    order_id, order_code = models.create_order(
        session["user_id"], restaurant["id"], address_id,
        item_total, delivery_fee, platform_fee, taxes, discount, applied_code, grand_total,
    )

    for item in cart_items:
        models.add_order_item(
            order_id, item["food_item_id"], item["name"], item["quantity"], item["price"], item["size"], item["extras"]
        )

    # ---- Demo payment: generate a fake transaction id ----
    models.create_payment(order_id, method, grand_total, status="success")

    # ---- Assign a random delivery partner and start the tracking simulation ----
    partner = models.pick_random_delivery_partner()
    if partner:
        models.assign_delivery_partner_to_order(order_id, partner["id"])
        models.create_tracking_row(order_id, restaurant["latitude"], restaurant["longitude"], 2.5, 25)

    # ---- Clear the cart and the applied coupon ----
    models.clear_cart(cart["id"])
    session.pop("applied_coupon", None)

    # ---- Notify the user ----
    models.create_notification(session["user_id"], order_id, "Your order has been placed.")

    return redirect(url_for("order_success", order_id=order_id))


# =====================================================================
# ORDER SUCCESS / HISTORY / TRACKING
# =====================================================================

@app.route("/order_success/<int:order_id>")
@login_required()
def order_success(order_id):
    order = models.get_order_by_id(order_id)
    if order is None or order["user_id"] != session["user_id"]:
        flash("Order not found.")
        return redirect(url_for("index"))

    items = models.get_order_items(order_id)
    restaurant = models.get_restaurant_by_id(order["restaurant_id"])
    address = models.get_address_by_id(order["address_id"]) if order["address_id"] else None
    payment = models.get_payment_for_order(order_id)

    return render_template(
        "order_success.html", order=order, items=items, restaurant=restaurant, address=address, payment=payment
    )


@app.route("/orders")
@login_required()
def orders_page():
    orders = models.get_orders_for_user(session["user_id"])
    orders_with_restaurant = []
    for order in orders:
        restaurant = models.get_restaurant_by_id(order["restaurant_id"])
        orders_with_restaurant.append((order, restaurant))
    return render_template("orders.html", orders_with_restaurant=orders_with_restaurant)


@app.route("/reorder/<int:order_id>", methods=["POST"])
@login_required()
def reorder(order_id):
    order = models.get_order_by_id(order_id)
    if order is None or order["user_id"] != session["user_id"]:
        flash("Order not found.")
        return redirect(url_for("orders_page"))

    items = models.get_order_items(order_id)
    cart = models.get_or_create_cart(session["user_id"], order["restaurant_id"])

    added_count = 0
    for item in items:
        food_item = models.get_food_item_by_id(item["food_item_id"])
        if food_item and food_item["is_available"]:
            models.add_item_to_cart(cart["id"], item["food_item_id"], item["quantity"], item["size"], item["extras"], 0, "")
            added_count += 1

    if added_count:
        flash("Items added to cart.")
    else:
        flash("Sorry, none of those items are available right now.")
    return redirect(url_for("cart_page"))


@app.route("/track_order/<int:order_id>")
@login_required()
def track_order(order_id):
    order = models.get_order_by_id(order_id)
    if order is None or order["user_id"] != session["user_id"]:
        flash("Order not found.")
        return redirect(url_for("orders_page"))

    restaurant = models.get_restaurant_by_id(order["restaurant_id"])
    address = models.get_address_by_id(order["address_id"]) if order["address_id"] else None
    tracking = models.get_tracking_for_order(order_id)
    partner = models.get_delivery_partner_by_id(order["delivery_partner_id"]) if order["delivery_partner_id"] else None

    status_steps = ["placed", "confirmed", "preparing", "ready", "assigned", "picked_up", "out_for_delivery", "delivered"]
    review = models.get_review_for_order(order_id)

    return render_template(
        "track_order.html",
        order=order, restaurant=restaurant, address=address, tracking=tracking,
        partner=partner, status_steps=status_steps, review=review,
    )


@app.route("/api/advance_order/<int:order_id>", methods=["POST"])
@login_required()
def api_advance_order(order_id):
    """
    Called by JavaScript every few seconds from the tracking page.
    Moves the simulated delivery partner one step closer and returns
    the new status + coordinates as JSON.
    """
    order = models.get_order_by_id(order_id)
    if order is None or order["user_id"] != session["user_id"]:
        return jsonify({"error": "not found"}), 404

    if order["status"] == "delivered":
        tracking = models.get_tracking_for_order(order_id)
        return jsonify({
            "status": "delivered", "lat": tracking["current_lat"], "lng": tracking["current_lng"],
            "distance_km": 0, "eta_minutes": 0,
        })

    new_status = models.advance_tracking_step(order_id)
    tracking = models.get_tracking_for_order(order_id)

    message = models.STATUS_MESSAGES.get(new_status, "")
    if message:
        models.create_notification(session["user_id"], order_id, message)

    return jsonify({
        "status": new_status,
        "lat": tracking["current_lat"],
        "lng": tracking["current_lng"],
        "distance_km": tracking["distance_remaining_km"],
        "eta_minutes": tracking["eta_minutes"],
    })


# =====================================================================
# REVIEWS
# =====================================================================

@app.route("/review/<int:order_id>", methods=["POST"])
@login_required()
def submit_review(order_id):
    order = models.get_order_by_id(order_id)
    if order is None or order["user_id"] != session["user_id"]:
        flash("Order not found.")
        return redirect(url_for("orders_page"))

    models.create_review(
        session["user_id"], order_id, order["restaurant_id"],
        int(request.form.get("restaurant_rating", 5)),
        int(request.form.get("food_rating", 5)),
        int(request.form.get("delivery_rating", 5)),
        request.form.get("comment", ""),
    )
    flash("Thank you for your review!")
    return redirect(url_for("track_order", order_id=order_id))


# =====================================================================
# FAVORITES PAGE
# =====================================================================

@app.route("/favorites")
@login_required()
def favorites_page():
    restaurants = models.get_favorite_restaurants(session["user_id"])
    foods = models.get_favorite_foods(session["user_id"])
    return render_template("favorites.html", restaurants=restaurants, foods=foods)


# =====================================================================
# PROFILE + NOTIFICATIONS
# =====================================================================

@app.route("/profile")
@login_required()
def profile_page():
    user = current_user()
    addresses = models.get_addresses_for_user(session["user_id"])
    notifications = models.get_notifications_for_user(session["user_id"])
    order_count = len(models.get_orders_for_user(session["user_id"]))
    return render_template("profile.html", user=user, addresses=addresses, notifications=notifications, order_count=order_count)


# =====================================================================
# ADMIN DASHBOARD
# =====================================================================

@app.route("/admin")
@login_required(role="admin")
def admin_dashboard():
    stats = models.get_admin_stats()
    restaurants = models.get_all_restaurants()
    orders = models.get_all_orders()
    coupons = models.get_all_active_coupons()
    payments = models.get_all_payments()
    delivery_partners = models.get_all_delivery_partners()

    orders_with_restaurant = [(o, models.get_restaurant_by_id(o["restaurant_id"])) for o in orders[:30]]

    return render_template(
        "admin.html", stats=stats, restaurants=restaurants, orders_with_restaurant=orders_with_restaurant,
        coupons=coupons, payments=payments[:30], delivery_partners=delivery_partners,
    )


@app.route("/admin/restaurant/toggle/<int:restaurant_id>", methods=["POST"])
@login_required(role="admin")
def admin_toggle_restaurant(restaurant_id):
    conn = models.get_db()
    restaurant = conn.execute("SELECT * FROM restaurant WHERE id = ?", (restaurant_id,)).fetchone()
    new_status = 0 if restaurant["is_open"] else 1
    conn.execute("UPDATE restaurant SET is_open = ? WHERE id = ?", (new_status, restaurant_id))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/restaurant/delete/<int:restaurant_id>", methods=["POST"])
@login_required(role="admin")
def admin_delete_restaurant(restaurant_id):
    conn = models.get_db()
    conn.execute("DELETE FROM food_item WHERE restaurant_id = ?", (restaurant_id,))
    conn.execute("DELETE FROM restaurant WHERE id = ?", (restaurant_id,))
    conn.commit()
    conn.close()
    flash("Restaurant deleted.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/order/status/<int:order_id>", methods=["POST"])
@login_required(role="admin")
def admin_update_order_status(order_id):
    new_status = request.form.get("status")
    models.update_order_status(order_id, new_status)
    order = models.get_order_by_id(order_id)
    message = models.STATUS_MESSAGES.get(new_status, "")
    if message:
        models.create_notification(order["user_id"], order_id, message)
    flash("Order status updated.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/coupon/add", methods=["POST"])
@login_required(role="admin")
def admin_add_coupon():
    conn = models.get_db()
    conn.execute(
        """INSERT INTO coupon (code, description, discount_type, discount_value, max_discount, min_order_value, expiry_date, is_active)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
        (
            request.form.get("code", "").upper(),
            request.form.get("description", ""),
            request.form.get("discount_type", "PERCENT"),
            int(request.form.get("discount_value", 10)),
            int(request.form.get("max_discount", 100)),
            int(request.form.get("min_order_value", 0)),
            request.form.get("expiry_date", "2026-12-31"),
        ),
    )
    conn.commit()
    conn.close()
    flash("Coupon added.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/coupon/delete/<int:coupon_id>", methods=["POST"])
@login_required(role="admin")
def admin_delete_coupon(coupon_id):
    conn = models.get_db()
    conn.execute("UPDATE coupon SET is_active = 0 WHERE id = ?", (coupon_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_dashboard"))


# =====================================================================
# DELIVERY PARTNER DASHBOARD
# =====================================================================

@app.route("/delivery")
@login_required(role="delivery")
def delivery_dashboard():
    # For the demo, the logged-in delivery user sees ALL active orders,
    # since we only seed one demo delivery-partner user account.
    conn = models.get_db()
    orders = conn.execute(
        """SELECT * FROM "order" WHERE status NOT IN ('delivered') ORDER BY created_at DESC"""
    ).fetchall()
    conn.close()

    orders_full = []
    for order in orders:
        restaurant = models.get_restaurant_by_id(order["restaurant_id"])
        customer = models.get_user_by_id(order["user_id"])
        address = models.get_address_by_id(order["address_id"]) if order["address_id"] else None
        orders_full.append((order, restaurant, customer, address))

    return render_template("delivery.html", orders_full=orders_full)


@app.route("/delivery/advance/<int:order_id>", methods=["POST"])
@login_required(role="delivery")
def delivery_advance(order_id):
    models.advance_tracking_step(order_id)
    return redirect(url_for("delivery_dashboard"))


# =====================================================================
# APP STARTUP
# =====================================================================

# Seed sample data automatically when a fresh deployment has no database file.
if not os.path.exists(DB_PATH):
    from seed_data import run as seed_demo_data

    seed_demo_data()

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
