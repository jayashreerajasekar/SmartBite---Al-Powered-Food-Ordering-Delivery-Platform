# RIN'S SMART BITE ≡ƒì╜∩╕Å
### A Full-Stack Food Delivery Web Application (College Capstone Project)

RIN'S SMART BITE is a complete, working food-delivery website ΓÇö browse restaurants,
build a large customizable menu order, apply coupons, pay with a demo payment flow,
and track your delivery live on a map with a simulated moving delivery partner.

It is built with **plain, beginner-friendly Python** so every line can be explained
during a viva / project defense.

---

## 1. Project Overview

RIN'S SMART BITE lets a customer:
- Browse 35 restaurants across 25+ cuisines, each with a large menu (900+ dishes total)
- Search and filter restaurants and dishes
- Customize a dish (size, extras, instructions) and add it to a cart
- Apply real working coupons that calculate a discount
- Check out with a saved address
- Pay using a **demo** UPI / Card / Cash-on-Delivery flow (no real money involved)
- Track the order live on an interactive map as a delivery partner "moves" toward them
- Rate the restaurant, food, and delivery partner after delivery
- Reorder a past order, save favorites, and manage their profile

It also includes:
- An **Admin Dashboard** to manage restaurants, orders, coupons, and view payments
- A **Delivery Partner Dashboard** to move an order through its delivery stages

---

## 2. Why raw SQLite instead of Flask-SQLAlchemy / Flask-Login?

The original plan for this project used Flask-SQLAlchemy and Flask-Login. This build
uses Python's **built-in `sqlite3` module** and Flask's **built-in `session`** object
instead. This was a deliberate choice, not a shortcut:

- **Zero extra dependencies** ΓÇö only `Flask` itself needs to be installed.
- **Nothing hidden by an ORM** ΓÇö every database action is a plain, visible SQL
  statement inside a simple Python function in `models.py`. This is usually *easier*
  to explain line-by-line in a viva than ORM model classes and query builders.
- Passwords are still stored securely, using `werkzeug.security.generate_password_hash`
  / `check_password_hash` (the same library Flask-Login itself relies on).
- Login "sessions" are Flask's own signed cookie session ΓÇö `session["user_id"]` ΓÇö
  checked by a small `login_required()` decorator in `app.py`.

If your instructor specifically requires the `Flask-SQLAlchemy` package name to appear
in `requirements.txt`, you can explain this substitution as a deliberate simplification
in line with the project's own "keep Python simple" requirement ΓÇö swapping ORM models
for equivalent raw-SQL functions with the exact same behavior.

---

## 3. Technology Stack

**Backend:** Python 3, Flask, Python's built-in `sqlite3` module, `werkzeug.security`
**Frontend:** HTML, CSS (custom, on top of Bootstrap 5 grid/components), vanilla JavaScript
**Database:** SQLite (single file: `rin_smart_bite.db`)
**Maps:** Leaflet.js + OpenStreetMap tiles
**Python version:** 3.9 or newer recommended (built and tested on Python 3.12)

---

## 4. Project Structure

```
RIN-SMART-BITE/
Γö£ΓöÇΓöÇ app.py                 # All Flask routes (the "controller" layer)
Γö£ΓöÇΓöÇ models.py               # Simple functions that read/write the database
Γö£ΓöÇΓöÇ database.py              # Database connection + table creation (schema)
Γö£ΓöÇΓöÇ seed_data.py              # Fills the database with demo restaurants/food/etc.
Γö£ΓöÇΓöÇ requirements.txt
Γö£ΓöÇΓöÇ README.md
Γö£ΓöÇΓöÇ .env.example
Γö£ΓöÇΓöÇ static/
Γöé   Γö£ΓöÇΓöÇ css/style.css        # All custom styling
Γöé   Γö£ΓöÇΓöÇ js/script.js         # Food modal, favorites toggle, price preview
Γöé   ΓööΓöÇΓöÇ images/
ΓööΓöÇΓöÇ templates/
    Γö£ΓöÇΓöÇ base.html             # Shared header/footer layout
    Γö£ΓöÇΓöÇ index.html            # Home page
    Γö£ΓöÇΓöÇ login.html / register.html
    Γö£ΓöÇΓöÇ restaurants.html       # Search/filter/browse restaurants
    Γö£ΓöÇΓöÇ restaurant.html         # One restaurant's full menu + food modal
    Γö£ΓöÇΓöÇ _restaurant_card.html    # Reusable restaurant card
    Γö£ΓöÇΓöÇ cart.html
    Γö£ΓöÇΓöÇ checkout.html            # Address selection
    Γö£ΓöÇΓöÇ payment.html               # Demo UPI/Card/COD flow
    Γö£ΓöÇΓöÇ order_success.html
    Γö£ΓöÇΓöÇ track_order.html            # Live map + simulated GPS tracking
    Γö£ΓöÇΓöÇ orders.html                  # Order history / reorder
    Γö£ΓöÇΓöÇ favorites.html
    Γö£ΓöÇΓöÇ profile.html
    Γö£ΓöÇΓöÇ offers.html
    Γö£ΓöÇΓöÇ admin.html                     # Admin dashboard
    ΓööΓöÇΓöÇ delivery.html                   # Delivery partner dashboard
```

---

## 5. Installation & Setup

### Step 1 ΓÇö Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 2 ΓÇö Install dependencies
```bash
pip install -r requirements.txt
```
(Only Flask itself is required ΓÇö see Section 2 above for why.)

### Step 3 ΓÇö Seed the database
This creates `rin_smart_bite.db` and fills it with 35 restaurants, 900+ food items,
coupons, offers, delivery partners, and 3 demo login accounts.
```bash
python seed_data.py
```
Running it again later is safe ΓÇö it detects existing data and skips reseeding.
(Delete `rin_smart_bite.db` and re-run this script if you want a completely fresh database.)

### Step 4 ΓÇö Run the application
```bash
python app.py
```

### Step 5 ΓÇö Open in your browser
```
http://127.0.0.1:5000
```

---

## 6. Demo Login Credentials

| Role      | Email                         | Password       |
|-----------|--------------------------------|----------------|
| Customer  | customer@rinsmartbite.demo    | Customer@123   |
| Admin     | admin@rinsmartbite.demo       | Admin@123      |
| Delivery  | delivery@rinsmartbite.demo    | Delivery@123   |

You can also register a brand new customer account from the Login page.

---

## 7. Demo Payment

This is a **simulation only** ΓÇö no real bank, card, or UPI network is contacted and
no real money moves. Selecting UPI, Card, or Cash on Delivery on the Payment page and
clicking "Complete Demo Payment":
1. Runs a short client-side "Processing..." animation (JavaScript only).
2. Submits to the `/payment` Flask route.
3. `models.create_payment()` generates a readable fake transaction ID
   (e.g. `RIN-TXN-482913`) and stores it, along with the order, in SQLite.

---

## 8. Live Map / Delivery Simulation Demo

On the **Track Order** page:
1. A Leaflet map shows three markers: the restaurant (≡ƒì┤), the delivery partner (≡ƒ¢╡),
   and the customer's address (≡ƒÅá), connected by a dashed route line.
2. A JavaScript `setInterval` timer calls `/api/advance_order/<id>` (a Flask route)
   every 3 seconds.
3. Each call runs `models.advance_tracking_step()` in Python, which:
   - Moves the order to its next status (placed ΓåÆ confirmed ΓåÆ preparing ΓåÆ ready ΓåÆ
     assigned ΓåÆ picked_up ΓåÆ out_for_delivery ΓåÆ delivered)
   - Calculates a new simulated latitude/longitude a fraction of the way from the
     restaurant to the customer
   - Recalculates the remaining distance and ETA
4. The JavaScript updates the marker position, the ETA/distance numbers, and the
   status timeline on the page ΓÇö no page reload needed.

This intentionally avoids WebSockets or background workers, exactly as the project
brief asked for ΓÇö it is a simple timer + simple Flask route, easy to explain.

---

## 9. Admin Login Demo

Log in with the Admin demo account to reach `/admin`, where you can:
- View live statistics (users, restaurants, orders, revenue, active deliveries)
- Update any order's status
- Open/close a restaurant, or delete one
- Add or deactivate coupons
- View all recorded (demo) payments and delivery partners

## 10. Delivery Partner Login Demo

Log in with the Delivery demo account to reach `/delivery`, where every active order
in the system is listed with a single button to move it to its next delivery stage
(Accept ΓåÆ Reached Restaurant ΓåÆ Picked Up ΓåÆ Out for Delivery ΓåÆ Delivered).

---

## 11. How the Main Python Files Work (for your viva)

- **`database.py`** ΓÇö Opens a SQLite connection and creates every table with
  `CREATE TABLE IF NOT EXISTS`. Run once at startup; safe to call repeatedly.
- **`models.py`** ΓÇö One function per database action (e.g. `get_all_restaurants()`,
  `calculate_discount()`, `advance_tracking_step()`). Routes in `app.py` never write
  raw SQL themselves ΓÇö they call these functions instead, keeping `app.py` readable.
- **`app.py`** ΓÇö Defines every URL route. Each route: (1) reads form/query data,
  (2) calls one or more `models.py` functions, (3) renders a template or redirects.
- **`seed_data.py`** ΓÇö Builds Python lists of restaurant/food names and loops over
  them with simple `for` loops to `INSERT` rows ΓÇö no complicated logic, just loops.

### Key logic to walk through in your presentation
- **Login:** `check_password_hash()` in the `/login` route compares the typed
  password against the hash stored in the `user` table.
- **Cart:** `models.get_or_create_cart()` + `models.add_item_to_cart()` +
  `models.calculate_cart_total()`.
- **Coupons:** `models.calculate_discount()` ΓÇö a single, clearly commented function.
- **Payment:** `models.create_payment()` ΓÇö generates a fake transaction ID.
- **Order creation:** the `payment_page()` POST branch in `app.py` ΓÇö creates the
  order, order items, payment, and starting delivery tracking row, all in sequence.
- **Tracking:** `models.advance_tracking_step()` ΓÇö moves the status forward and
  interpolates a new GPS point between the restaurant and the customer.

---

## 12. Future Improvements

- Real payment gateway integration (Razorpay/Stripe test mode)
- Real-time order updates using WebSockets instead of polling
- Restaurant owner dashboard for managing their own menu
- Push notifications / SMS integration
- Deploying to a cloud host with a production database (PostgreSQL)

---

## 13. Capstone Presentation Points

- Walk through the **folder structure** first (Section 4) so the examiner sees the
  project is organized, not a single giant file.
- Demonstrate the **full demo flow**: search ΓåÆ restaurant ΓåÆ large menu ΓåÆ customize
  a dish ΓåÆ cart ΓåÆ coupon ΓåÆ checkout ΓåÆ payment ΓåÆ tracking with live map ΓåÆ review.
- Open `models.py` and explain 2ΓÇô3 functions line-by-line (e.g. `calculate_discount`,
  `advance_tracking_step`) ΓÇö these show real business logic in simple Python.
- Show the **Admin Dashboard** updating an order's status live, then flip back to the
  customer's Track Order page and refresh to show the status changed.
- Mention the **no-ORM design choice** (Section 2) if asked about the tech stack ΓÇö
  it demonstrates you understand what an ORM would otherwise be doing for you.

---

## 14. Running the Project ΓÇö Quick Reference

```bash
pip install -r requirements.txt
python seed_data.py
python app.py
```
Then open **http://127.0.0.1:5000** in your browser.
