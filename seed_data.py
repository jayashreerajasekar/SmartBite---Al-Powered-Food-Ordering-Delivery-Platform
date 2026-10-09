"""
seed_data.py
------------
Run this file ONCE (python seed_data.py) to fill the database with demo
data: restaurants, food categories, food items, coupons, offers, delivery
partners, and three demo login accounts (customer, admin, delivery).

The code below is simple Python loops - no complicated logic. We build
lists of realistic Indian restaurant/food names, then loop over them and
INSERT each one into the database.
"""

import random
from werkzeug.security import generate_password_hash
from database import get_db, init_db

# Reusable food photos (Unsplash), grouped by cuisine/category so every
# food item gets a picture that actually matches its category.
IMAGES = {
    "biryani": [
        "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=500",
        "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=500",
        "https://images.unsplash.com/photo-1701579231378-3728850a9d0f?w=500",
    ],
    "pizza": [
        "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500",
        "https://images.unsplash.com/photo-1548369937-47519962c11a?w=500",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=500",
    ],
    "burger": [
        "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500",
        "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=500",
        "https://images.unsplash.com/photo-1550547660-d9450f859349?w=500",
    ],
    "south_indian": [
        "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=500",
        "https://images.unsplash.com/photo-1630383249896-483b8990e816?w=500",
        "https://images.unsplash.com/photo-1610192244261-3f33de3f72e1?w=500",
    ],
    "north_indian": [
        "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500",
        "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500",
        "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500",
    ],
    "chinese": [
        "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=500",
        "https://images.unsplash.com/photo-1585851373190-74e262c5b5c4?w=500",
        "https://images.unsplash.com/photo-1626804475297-41608ea09aeb?w=500",
    ],
    "dessert": [
        "https://images.unsplash.com/photo-1551024506-0bccd828d307?w=500",
        "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=500",
        "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=500",
    ],
    "beverage": [
        "https://images.unsplash.com/photo-1544145945-f90425340c7e?w=500",
        "https://images.unsplash.com/photo-1541658016709-82535e94bc69?w=500",
        "https://images.unsplash.com/photo-1497534446932-c925b458314e?w=500",
    ],
    "shawarma": [
        "https://images.unsplash.com/photo-1662116765813-42db8a11e6d2?w=500",
        "https://images.unsplash.com/photo-1633478062482-790e3b5dd810?w=500",
    ],
    "seafood": [
        "https://images.unsplash.com/photo-1559847844-5315695dadae?w=500",
        "https://images.unsplash.com/photo-1615141982883-c7ad0e69fd62?w=500",
    ],
    "bakery": [
        "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500",
        "https://images.unsplash.com/photo-1517433670267-08bbd4be890f?w=500",
    ],
    "salad": [
        "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500",
    ],
    "default": [
        "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500",
    ],
}

RESTAURANT_COVER_IMAGES = [
    "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800",
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800",
    "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800",
    "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=800",
    "https://images.unsplash.com/photo-1544148103-0773bf10d330?w=800",
    "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=800",
]

CATEGORIES = [
    ("Biryani", "biryani"), ("Pizza", "pizza"), ("Burger", "burger"),
    ("South Indian", "south_indian"), ("North Indian", "north_indian"),
    ("Chinese", "chinese"), ("Desserts", "dessert"), ("Cakes", "dessert"),
    ("Ice Cream", "dessert"), ("Shawarma", "shawarma"), ("Rolls", "north_indian"),
    ("Dosa", "south_indian"), ("Idli", "south_indian"), ("Parotta", "south_indian"),
    ("Fried Rice", "chinese"), ("Noodles", "chinese"), ("Meals", "south_indian"),
    ("Seafood", "seafood"), ("Chicken", "north_indian"), ("Vegetarian", "north_indian"),
    ("Beverages", "beverage"), ("Coffee", "beverage"), ("Fast Food", "burger"),
    ("Bakery", "bakery"), ("Arabian", "shawarma"), ("Mexican", "burger"),
    ("Continental", "salad"),
]

# (restaurant name, cuisine, is_veg_only)
RESTAURANT_NAMES = [
    ("Annapoorna Grand", "South Indian", 0),
    ("Sangeetha Veg Restaurant", "South Indian, Veg", 1),
    ("Empire Biryani House", "Biryani, Mughlai", 0),
    ("Paradise Biryani Point", "Biryani, Hyderabadi", 0),
    ("Domino's Pizza Corner", "Pizza, Italian", 0),
    ("Pizza Republic", "Pizza, Fast Food", 0),
    ("Burger Barn", "Burgers, American", 0),
    ("The Burger Factory", "Burgers, Fast Food", 0),
    ("Dragon Wok Chinese", "Chinese, Asian", 0),
    ("Mainland Wok Express", "Chinese, Thai", 0),
    ("Saravana Bhavan", "South Indian, Veg", 1),
    ("Adyar Ananda Bhavan (A2B)", "South Indian, Sweets", 1),
    ("Punjabi Tadka", "North Indian, Punjabi", 0),
    ("Copper Chimney", "North Indian, Mughlai", 0),
    ("Al Baik Shawarma", "Arabian, Shawarma", 0),
    ("Turkish Delight Shawarma", "Arabian, Continental", 0),
    ("Ocean Catch Seafood", "Seafood, Coastal", 0),
    ("Malabar Fish Curry House", "Seafood, Kerala", 0),
    ("KFC Fried Chicken", "Fast Food, Chicken", 0),
    ("Chicken Republic", "Chicken, Fast Food", 0),
    ("Green Leaf Vegetarian", "Vegetarian, Healthy", 1),
    ("Pure Veg Delight", "Vegetarian, North Indian", 1),
    ("Cafe Coffee Day", "Beverages, Coffee", 1),
    ("Third Wave Coffee", "Coffee, Continental", 1),
    ("Hot Breads Bakery", "Bakery, Cakes", 1),
    ("Monginis Cake Shop", "Bakery, Desserts", 1),
    ("Taco Bell Fiesta", "Mexican, Fast Food", 0),
    ("El Mexicano Grill", "Mexican, Continental", 0),
    ("Naturals Ice Cream", "Ice Cream, Desserts", 1),
    ("Amaravathi Restaurant", "Andhra, Biryani", 0),
    ("Anjappar Chettinad", "Chettinad, South Indian", 0),
    ("The Grand Sweets", "Sweets, Desserts", 1),
    ("Rolls Junction", "Rolls, Fast Food", 0),
    ("Parotta Nation", "Parotta, South Indian", 0),
    ("Noodle House Express", "Noodles, Chinese", 0),
]

# (item name, category_key_for_image, base_price, is_veg)
FOOD_TEMPLATES = {
    "Recommended": [
        ("Chef's Special Combo", "default", 249, 1),
        ("House Special Platter", "default", 299, 0),
    ],
    "Starters": [
        ("Paneer Tikka", "north_indian", 220, 1),
        ("Chicken 65", "chinese", 240, 0),
        ("Veg Manchurian", "chinese", 190, 1),
        ("Chilli Chicken", "chinese", 250, 0),
        ("Gobi Manchurian", "chinese", 180, 1),
        ("Chicken Lollipop", "chinese", 260, 0),
        ("Spring Rolls", "chinese", 170, 1),
    ],
    "Main Course": [
        ("Butter Chicken", "north_indian", 320, 0),
        ("Paneer Butter Masala", "north_indian", 270, 1),
        ("Dal Makhani", "north_indian", 210, 1),
        ("Kadai Chicken", "north_indian", 300, 0),
        ("Chana Masala", "north_indian", 190, 1),
        ("Mutton Rogan Josh", "north_indian", 380, 0),
        ("Palak Paneer", "north_indian", 240, 1),
    ],
    "Biryani": [
        ("Chicken Biryani", "biryani", 260, 0),
        ("Mutton Biryani", "biryani", 340, 0),
        ("Veg Biryani", "biryani", 200, 1),
        ("Egg Biryani", "biryani", 220, 0),
        ("Prawns Biryani", "biryani", 360, 0),
        ("Hyderabadi Biryani", "biryani", 300, 0),
    ],
    "Rice": [
        ("Jeera Rice", "south_indian", 150, 1),
        ("Curd Rice", "south_indian", 130, 1),
        ("Lemon Rice", "south_indian", 140, 1),
        ("Ghee Rice", "south_indian", 160, 1),
    ],
    "Chinese": [
        ("Veg Fried Rice", "chinese", 180, 1),
        ("Chicken Fried Rice", "chinese", 220, 0),
        ("Schezwan Fried Rice", "chinese", 200, 1),
        ("Egg Fried Rice", "chinese", 190, 0),
    ],
    "Noodles": [
        ("Veg Hakka Noodles", "chinese", 180, 1),
        ("Chicken Noodles", "chinese", 220, 0),
        ("Schezwan Noodles", "chinese", 200, 1),
    ],
    "South Indian": [
        ("Masala Dosa", "south_indian", 120, 1),
        ("Plain Dosa", "south_indian", 90, 1),
        ("Onion Rava Dosa", "south_indian", 140, 1),
        ("Idli Sambar (4 pcs)", "south_indian", 80, 1),
        ("Medu Vada (2 pcs)", "south_indian", 70, 1),
        ("Pongal", "south_indian", 100, 1),
        ("Uttapam", "south_indian", 130, 1),
        ("Parotta (2 pcs)", "south_indian", 90, 1),
        ("Chicken Chettinad", "south_indian", 300, 0),
    ],
    "North Indian": [
        ("Butter Naan", "north_indian", 50, 1),
        ("Tandoori Roti", "north_indian", 30, 1),
        ("Chole Bhature", "north_indian", 180, 1),
        ("Rajma Chawal", "north_indian", 190, 1),
        ("Tandoori Chicken (Half)", "north_indian", 280, 0),
    ],
    "Breads": [
        ("Garlic Naan", "north_indian", 60, 1),
        ("Butter Roti", "north_indian", 35, 1),
        ("Laccha Paratha", "north_indian", 55, 1),
    ],
    "Desserts": [
        ("Gulab Jamun (2 pcs)", "dessert", 90, 1),
        ("Rasmalai (2 pcs)", "dessert", 110, 1),
        ("Chocolate Brownie", "dessert", 130, 1),
        ("Vanilla Ice Cream", "dessert", 80, 1),
        ("Gajar Ka Halwa", "dessert", 100, 1),
    ],
    "Beverages": [
        ("Sweet Lassi", "beverage", 80, 1),
        ("Masala Chai", "beverage", 40, 1),
        ("Cold Coffee", "beverage", 110, 1),
        ("Fresh Lime Soda", "beverage", 70, 1),
        ("Filter Coffee", "beverage", 50, 1),
        ("Mango Lassi", "beverage", 90, 1),
    ],
}

PIZZA_ITEMS = [
    ("Margherita Pizza", "pizza", 249, 1),
    ("Farmhouse Pizza", "pizza", 329, 1),
    ("Chicken Pepperoni Pizza", "pizza", 399, 0),
    ("Peppy Paneer Pizza", "pizza", 319, 1),
    ("Chicken Tikka Pizza", "pizza", 379, 0),
    ("Cheese Burst Pizza", "pizza", 349, 1),
    ("Veggie Supreme Pizza", "pizza", 339, 1),
    ("BBQ Chicken Pizza", "pizza", 409, 0),
]

BURGER_ITEMS = [
    ("Classic Veg Burger", "burger", 99, 1),
    ("Crispy Chicken Burger", "burger", 149, 0),
    ("Cheese Blast Burger", "burger", 129, 1),
    ("Double Patty Burger", "burger", 189, 0),
    ("Paneer Tikka Burger", "burger", 139, 1),
    ("Spicy Chicken Zinger", "burger", 169, 0),
    ("French Fries", "burger", 90, 1),
    ("Cold Drink", "beverage", 50, 1),
]

SHAWARMA_ITEMS = [
    ("Chicken Shawarma Roll", "shawarma", 150, 0),
    ("Veg Shawarma Roll", "shawarma", 120, 1),
    ("Falafel Wrap", "shawarma", 140, 1),
    ("Hummus with Pita", "shawarma", 130, 1),
    ("Al Faham Chicken Plate", "shawarma", 260, 0),
]

SEAFOOD_ITEMS = [
    ("Fish Curry Meals", "seafood", 260, 0),
    ("Prawns Masala", "seafood", 320, 0),
    ("Grilled Fish", "seafood", 340, 0),
    ("Crab Masala", "seafood", 380, 0),
    ("Fish Fry", "seafood", 220, 0),
]

BAKERY_ITEMS = [
    ("Chocolate Cake Slice", "bakery", 90, 1),
    ("Red Velvet Pastry", "bakery", 100, 1),
    ("Croissant", "bakery", 70, 1),
    ("Blueberry Muffin", "bakery", 80, 1),
    ("Cheese Sandwich", "bakery", 110, 1),
]

EXTRAS_POOL = [
    ("Extra Cheese", 40), ("Extra Chicken", 80), ("Extra Sauce", 20), ("Extra Raita", 15),
]


def pick_image(category_key):
    pool = IMAGES.get(category_key, IMAGES["default"])
    return random.choice(pool)


def build_menu_for_restaurant(cuisine_text):
    """
    Build a list of (menu_section, name, category_key, price, is_veg) for
    one restaurant, choosing template groups based on its cuisine text.
    Every restaurant ends up with roughly 25-35 items.
    """
    cuisine_lower = cuisine_text.lower()
    menu = []

    # Everyone gets a "Recommended" section and beverages/desserts
    for section in ["Recommended", "Beverages", "Desserts"]:
        for item in FOOD_TEMPLATES[section]:
            menu.append((section, *item))

    if "biryani" in cuisine_lower or "hyderabadi" in cuisine_lower or "andhra" in cuisine_lower:
        for item in FOOD_TEMPLATES["Biryani"]:
            menu.append(("Biryani", *item))
        for item in FOOD_TEMPLATES["Rice"]:
            menu.append(("Rice", *item))
        for item in FOOD_TEMPLATES["Starters"]:
            menu.append(("Starters", *item))

    if "south indian" in cuisine_lower or "chettinad" in cuisine_lower or "kerala" in cuisine_lower:
        for item in FOOD_TEMPLATES["South Indian"]:
            menu.append(("South Indian", *item))
        for item in FOOD_TEMPLATES["Rice"]:
            menu.append(("Rice", *item))

    if "north indian" in cuisine_lower or "punjabi" in cuisine_lower or "mughlai" in cuisine_lower:
        for item in FOOD_TEMPLATES["North Indian"]:
            menu.append(("North Indian", *item))
        for item in FOOD_TEMPLATES["Main Course"]:
            menu.append(("Main Course", *item))
        for item in FOOD_TEMPLATES["Breads"]:
            menu.append(("Breads", *item))
        for item in FOOD_TEMPLATES["Starters"]:
            menu.append(("Starters", *item))

    if "chinese" in cuisine_lower or "asian" in cuisine_lower or "thai" in cuisine_lower:
        for item in FOOD_TEMPLATES["Chinese"]:
            menu.append(("Chinese", *item))
        for item in FOOD_TEMPLATES["Noodles"]:
            menu.append(("Noodles", *item))
        for item in FOOD_TEMPLATES["Starters"]:
            menu.append(("Starters", *item))

    if "pizza" in cuisine_lower or "italian" in cuisine_lower:
        for item in PIZZA_ITEMS:
            menu.append(("Pizza", *item))

    if "burger" in cuisine_lower or "fast food" in cuisine_lower or "american" in cuisine_lower:
        for item in BURGER_ITEMS:
            menu.append(("Burgers", *item))

    if "shawarma" in cuisine_lower or "arabian" in cuisine_lower:
        for item in SHAWARMA_ITEMS:
            menu.append(("Shawarma", *item))

    if "seafood" in cuisine_lower or "coastal" in cuisine_lower:
        for item in SEAFOOD_ITEMS:
            menu.append(("Seafood", *item))

    if "bakery" in cuisine_lower or "cakes" in cuisine_lower or "sweets" in cuisine_lower:
        for item in BAKERY_ITEMS:
            menu.append(("Bakery", *item))

    if "chicken" in cuisine_lower:
        for item in FOOD_TEMPLATES["Main Course"]:
            menu.append(("Main Course", *item))

    if "vegetarian" in cuisine_lower or "veg" in cuisine_lower:
        # Keep only veg items for veg-only restaurants (filter later at insert time)
        pass

    if "coffee" in cuisine_lower:
        for item in FOOD_TEMPLATES["Beverages"]:
            menu.append(("Beverages", *item))
        for item in BAKERY_ITEMS:
            menu.append(("Bakery", *item))

    if "mexican" in cuisine_lower:
        menu.append(("Mexican", "Chicken Tacos", "burger", 180, 0))
        menu.append(("Mexican", "Veg Burrito", "burger", 170, 1))
        menu.append(("Mexican", "Nachos Supreme", "burger", 160, 1))
        menu.append(("Mexican", "Quesadilla", "burger", 190, 1))

    if "rolls" in cuisine_lower:
        menu.append(("Rolls", "Chicken Kathi Roll", "north_indian", 130, 0))
        menu.append(("Rolls", "Paneer Roll", "north_indian", 110, 1))
        menu.append(("Rolls", "Egg Roll", "north_indian", 100, 0))

    if "parotta" in cuisine_lower:
        menu.append(("Parotta", "Kothu Parotta", "south_indian", 140, 0))
        menu.append(("Parotta", "Veg Kothu Parotta", "south_indian", 120, 1))

    if "noodles" in cuisine_lower:
        for item in FOOD_TEMPLATES["Noodles"]:
            menu.append(("Noodles", *item))

    if "ice cream" in cuisine_lower:
        menu.append(("Ice Cream", "Chocolate Sundae", "dessert", 120, 1))
        menu.append(("Ice Cream", "Butterscotch Tub", "dessert", 150, 1))
        menu.append(("Ice Cream", "Strawberry Cone", "dessert", 60, 1))
        menu.append(("Ice Cream", "Kulfi Stick", "dessert", 50, 1))
        flavours = ["Vanilla", "Chocolate Chip", "Mango", "Butterscotch", "Black Currant",
                    "Pista", "Rajbhog", "Cookies & Cream", "Fruit & Nut", "Anjeer", "Rose", "Litchi"]
        for flavour in flavours:
            menu.append(("Ice Cream", f"{flavour} Ice Cream Scoop", "dessert", random.choice([60, 70, 80, 90]), 1))

    # Top up small/niche menus (bakeries, coffee shops, etc.) so every
    # restaurant still ends up with a reasonably large, browsable menu.
    filler_pool = [
        ("Veg Sandwich", "Beverages", "bakery", 90, 1), ("Cheese Toast", "Beverages", "bakery", 100, 1),
        ("Cold Brew Coffee", "Beverages", "beverage", 120, 1), ("Hot Chocolate", "Beverages", "beverage", 110, 1),
        ("Iced Tea", "Beverages", "beverage", 90, 1), ("Veg Puff", "Recommended", "bakery", 40, 1),
        ("Chicken Puff", "Recommended", "bakery", 50, 0), ("Donut", "Desserts", "dessert", 70, 1),
        ("Muffin", "Desserts", "bakery", 80, 1), ("Cupcake", "Desserts", "dessert", 75, 1),
        ("Fruit Salad", "Desserts", "dessert", 100, 1), ("Masala Papad", "Starters", "south_indian", 40, 1),
        ("Veg Cutlet", "Starters", "north_indian", 90, 1), ("Paneer Roll", "Rolls", "north_indian", 110, 1),
    ]
    idx = 0
    while len(menu) < 24 and idx < len(filler_pool) * 2:
        name, section, cat_key, price, is_veg = filler_pool[idx % len(filler_pool)]
        menu.append((section, name, cat_key, price, is_veg))
        idx += 1

    return menu


def run():
    print("Creating tables...")
    init_db()

    conn = get_db()
    cur = conn.cursor()

    # If already seeded, do nothing (safe to re-run seed_data.py)
    existing = cur.execute("SELECT COUNT(*) AS c FROM restaurant").fetchone()["c"]
    if existing > 0:
        print("Database already contains data - skipping seed.")
        conn.close()
        return

    print("Seeding food categories...")
    for name, key in CATEGORIES:
        cur.execute(
            "INSERT INTO food_category (name, image) VALUES (?, ?)",
            (name, pick_image(key)),
        )
    conn.commit()

    print("Seeding restaurants and menus...")
    restaurant_ids = []
    for i, (name, cuisine, is_veg_only) in enumerate(RESTAURANT_NAMES):
        rating = round(random.uniform(3.6, 4.9), 1)
        review_count = random.randint(120, 4800)
        price_for_two = random.choice([200, 250, 300, 350, 400, 450, 500])
        delivery_time = random.choice([20, 25, 30, 35, 40, 45])
        delivery_fee = random.choice([0, 20, 30, 40])
        distance_km = round(random.uniform(0.8, 6.5), 1)
        offer_choices = [
            "50% OFF up to Rs.100", "20% OFF on orders above Rs.299", "FREE DELIVERY",
            "Buy 1 Get 1 on Starters", "Flat Rs.125 OFF", None, None,
        ]
        offer_text = random.choice(offer_choices)
        # Spread restaurants around Coimbatore, Tamil Nadu for the map demo
        lat = 11.0168 + random.uniform(-0.05, 0.05)
        lng = 76.9558 + random.uniform(-0.05, 0.05)

        cur.execute(
            """INSERT INTO restaurant
               (name, cover_image, logo_image, cuisine, rating, review_count, price_for_two,
                delivery_time, delivery_fee, distance_km, address, opening_hours, offer_text,
                description, is_veg_only, is_open, latitude, longitude)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name,
                random.choice(RESTAURANT_COVER_IMAGES),
                random.choice(RESTAURANT_COVER_IMAGES),
                cuisine,
                rating,
                review_count,
                price_for_two,
                delivery_time,
                delivery_fee,
                distance_km,
                f"{random.randint(1,200)}, {random.choice(['Avinashi Road','RS Puram','Gandhipuram','Race Course','Peelamedu','Saibaba Colony'])}, Coimbatore",
                "9:00 AM - 11:00 PM",
                offer_text,
                f"{name} serves delicious {cuisine} dishes made fresh every day, loved by thousands of happy customers.",
                is_veg_only,
                1,
                lat,
                lng,
            ),
        )
        restaurant_id = cur.lastrowid
        restaurant_ids.append(restaurant_id)

        menu = build_menu_for_restaurant(cuisine)
        # De-duplicate items within the same restaurant/section
        seen = set()
        final_menu = []
        for section, item_name, cat_key, price, is_veg in menu:
            key = (section, item_name)
            if key in seen:
                continue
            seen.add(key)
            if is_veg_only and is_veg == 0:
                continue  # Skip non-veg items for veg-only restaurants
            final_menu.append((section, item_name, cat_key, price, is_veg))

        for section, item_name, cat_key, price, is_veg in final_menu:
            item_rating = round(random.uniform(3.5, 4.9), 1)
            calories = random.randint(150, 750)
            prep_time = random.randint(10, 35)
            price_variation = random.choice([0, 0, 0, 10, -10, 20])
            final_price = max(30, price + price_variation)

            # Find matching category id (best effort, defaults to NULL)
            category_row = cur.execute(
                "SELECT id FROM food_category WHERE name = ?", (section,)
            ).fetchone()
            category_id = category_row["id"] if category_row else None

            cur.execute(
                """INSERT INTO food_item
                   (restaurant_id, category_id, menu_section, name, description, price, image,
                    rating, is_veg, calories, prep_time, is_available)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (
                    restaurant_id, category_id, section, item_name,
                    f"Freshly prepared {item_name} - a customer favorite at {name}.",
                    final_price, pick_image(cat_key), item_rating, is_veg, calories, prep_time,
                ),
            )
    conn.commit()
    print(f"Seeded {len(restaurant_ids)} restaurants.")

    print("Seeding coupons...")
    coupons = [
        ("RIN50", "50% OFF up to Rs.100", "PERCENT", 50, 100, 299, "2026-12-31"),
        ("WELCOME125", "Rs.125 OFF on your order", "FLAT", 125, 125, 499, "2026-12-31"),
        ("RIN20", "20% OFF up to Rs.150", "PERCENT", 20, 150, 199, "2026-12-31"),
        ("FIRSTORDER", "Rs.100 OFF on first order", "FLAT", 100, 100, 249, "2026-12-31"),
    ]
    for code, desc, dtype, value, max_disc, min_order, expiry in coupons:
        cur.execute(
            """INSERT INTO coupon (code, description, discount_type, discount_value, max_discount, min_order_value, expiry_date, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
            (code, desc, dtype, value, max_disc, min_order, expiry),
        )
    conn.commit()

    print("Seeding offers...")
    offers = [
        ("50% OFF up to Rs.100", "On your first 3 orders", "RIN50", IMAGES["biryani"][0]),
        ("Rs.125 OFF", "On your first order above Rs.499", "WELCOME125", IMAGES["pizza"][0]),
        ("FREE DELIVERY", "On all orders this weekend", "RIN20", IMAGES["burger"][0]),
        ("20% OFF selected restaurants", "Maximum discount Rs.150", "RIN20", IMAGES["chinese"][0]),
        ("BUY 1 GET 1", "On select starters, weekends only", "FIRSTORDER", IMAGES["dessert"][0]),
        ("Weekend Special", "Flat Rs.100 off on orders above Rs.249", "FIRSTORDER", IMAGES["shawarma"][0]),
    ]
    for title, desc, code, image in offers:
        cur.execute(
            "INSERT INTO offer (title, description, coupon_code, image) VALUES (?, ?, ?, ?)",
            (title, desc, code, image),
        )
    conn.commit()

    print("Seeding delivery partners...")
    partners = [
        ("Arun Kumar", "9876543210", "Bike", "TN 09 AB 1234"),
        ("Vignesh Raj", "9876543211", "Bike", "TN 37 CD 5678"),
        ("Karthik S", "9876543212", "Scooter", "TN 66 EF 9012"),
        ("Manoj Prasad", "9876543213", "Bike", "TN 09 GH 3456"),
        ("Suresh Babu", "9876543214", "Bike", "TN 37 IJ 7890"),
        ("Praveen Kumar", "9876543215", "Scooter", "TN 66 KL 2345"),
    ]
    for name, phone, vehicle, number in partners:
        cur.execute(
            """INSERT INTO delivery_partner (name, phone, rating, vehicle_type, vehicle_number, avatar)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, phone, round(random.uniform(4.5, 5.0), 1), vehicle, number,
             "https://api.dicebear.com/7.x/avataaars/svg?seed=" + name.replace(" ", "")),
        )
    conn.commit()

    print("Seeding demo accounts...")
    demo_accounts = [
        ("Demo Customer", "customer@rinsmartbite.demo", "9000000001", "Customer@123", "customer"),
        ("Admin User", "admin@rinsmartbite.demo", "9000000002", "Admin@123", "admin"),
        ("Delivery Partner Demo", "delivery@rinsmartbite.demo", "9000000003", "Delivery@123", "delivery"),
    ]
    for name, email, phone, password, role in demo_accounts:
        cur.execute(
            "INSERT INTO user (name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (name, email, phone, generate_password_hash(password), role),
        )
    conn.commit()

    conn.close()
    print("Seeding complete!")


if __name__ == "__main__":
    run()
