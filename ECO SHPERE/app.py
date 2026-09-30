from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path

# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = "eco-sphere-secret-key-2026"

# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "store.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():

    conn = sqlite3.connect(str(DATABASE))

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = get_db()

    # -----------------------------------------------------
    # PRODUCTS TABLE
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image TEXT,
            image2 TEXT
        )
    """)

    conn.commit()

    # -----------------------------------------------------
    # CHECK DATABASE COLUMNS
    # -----------------------------------------------------

    columns = conn.execute(
        "PRAGMA table_info(products)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    # Add image column if old database doesn't have it
    if "image" not in column_names:

        conn.execute(
            "ALTER TABLE products ADD COLUMN image TEXT"
        )

        conn.commit()

    # Add image2 column if old database doesn't have it
    if "image2" not in column_names:

        conn.execute(
            "ALTER TABLE products ADD COLUMN image2 TEXT"
        )

        conn.commit()

    # -----------------------------------------------------
    # PRODUCT IMAGE DATA
    # -----------------------------------------------------

    product_data = [

        (
            "Wireless Headphones",
            "Premium wireless headphones with clear sound and comfortable design.",
            1999,

            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80",

            "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=800&q=80"
        ),

        (
            "Smart Watch",
            "Modern smart watch with fitness tracking and stylish design.",
            2499,

            "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80",

            "https://images.unsplash.com/photo-1508057198894-247b23fe5ade?auto=format&fit=crop&w=800&q=80"
        ),

        (
            "Running Shoes",
            "Comfortable running shoes suitable for sports and daily activities.",
            1799,

            "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",

            "https://images.unsplash.com/photo-1460353581641-37baddab0fa2?auto=format&fit=crop&w=800&q=80"
        ),

        (
            "Laptop",
            "Powerful and lightweight laptop for study, work and entertainment.",
            54999,

            "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=800&q=80",

            "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=800&q=80"
        ),

        (
            "Smartphone",
            "Modern smartphone with a high-quality display and powerful performance.",
            24999,

            "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=800&q=80",

            "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=800&q=80"
        )
    ]

    # -----------------------------------------------------
    # CHECK IF PRODUCTS EXIST
    # -----------------------------------------------------

    count = conn.execute(
        "SELECT COUNT(*) AS total FROM products"
    ).fetchone()["total"]

    # -----------------------------------------------------
    # INSERT PRODUCTS IF DATABASE IS EMPTY
    # -----------------------------------------------------

    if count == 0:

        for name, description, price, image, image2 in product_data:

            conn.execute("""
                INSERT INTO products
                (name, description, price, image, image2)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                description,
                price,
                image,
                image2
            ))

    # -----------------------------------------------------
    # UPDATE EXISTING PRODUCTS
    # -----------------------------------------------------

    else:

        for name, description, price, image, image2 in product_data:

            existing = conn.execute("""
                SELECT id
                FROM products
                WHERE name = ?
            """, (name,)).fetchone()

            if existing:

                conn.execute("""
                    UPDATE products
                    SET
                        description = ?,
                        price = ?,
                        image = ?,
                        image2 = ?
                    WHERE name = ?
                """, (
                    description,
                    price,
                    image,
                    image2,
                    name
                ))

            else:

                conn.execute("""
                    INSERT INTO products
                    (name, description, price, image, image2)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    name,
                    description,
                    price,
                    image,
                    image2
                ))

    conn.commit()

    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    conn = get_db()

    products = conn.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    cart_count = len(session.get("cart", []))

    return render_template(
        "index.html",
        products=products,
        cart_count=cart_count
    )


# =========================================================
# PRODUCTS
# =========================================================

@app.route("/products")
def products():

    conn = get_db()

    products = conn.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    cart_count = len(session.get("cart", []))

    return render_template(
        "products.html",
        products=products,
        cart_count=cart_count
    )


# =========================================================
# PRODUCT DETAILS
# =========================================================

@app.route("/product/<int:product_id>")
def product(product_id):

    conn = get_db()

    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    conn.close()

    if product is None:

        return "Product not found", 404

    cart_count = len(session.get("cart", []))

    return render_template(
        "product.html",
        product=product,
        cart_count=cart_count
    )


# =========================================================
# ADD TO CART
# =========================================================

@app.route("/add-to-cart/<int:product_id>", methods=["GET", "POST"])
def add_to_cart(product_id):

    # Create cart
    if "cart" not in session:

        session["cart"] = []

    cart = session["cart"]

    # Add product only if it is not already there
    if product_id not in cart:

        cart.append(product_id)

    session["cart"] = cart

    session.modified = True

    # Return to previous page if possible
    return redirect(
        request.referrer or url_for("products")
    )


# =========================================================
# CART
# =========================================================

@app.route("/cart")
def cart():

    cart_ids = session.get("cart", [])

    products = []

    total = 0

    if cart_ids:

        conn = get_db()

        # Remove invalid IDs
        valid_ids = []

        for product_id in cart_ids:

            try:

                valid_ids.append(int(product_id))

            except:

                pass

        if valid_ids:

            placeholders = ",".join(
                ["?"] * len(valid_ids)
            )

            products = conn.execute(
                f"""
                SELECT *
                FROM products
                WHERE id IN ({placeholders})
                """,
                valid_ids
            ).fetchall()

        conn.close()

    # Calculate total
    for product in products:

        total += float(product["price"])

    return render_template(
        "cart.html",
        products=products,
        total=total,
        cart_count=len(cart_ids)
    )


# =========================================================
# REMOVE FROM CART
# =========================================================

@app.route("/remove-from-cart/<int:product_id>")
def remove_from_cart(product_id):

    cart = session.get("cart", [])

    if product_id in cart:

        cart.remove(product_id)

    session["cart"] = cart

    session.modified = True

    return redirect(url_for("cart"))


# =========================================================
# CLEAR CART
# =========================================================

@app.route("/clear-cart")
def clear_cart():

    session["cart"] = []

    session.modified = True

    return redirect(url_for("cart"))


# =========================================================
# CHECKOUT
# =========================================================

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    cart_ids = session.get("cart", [])

    products = []

    total = 0

    if cart_ids:

        conn = get_db()

        valid_ids = []

        for product_id in cart_ids:

            try:

                valid_ids.append(int(product_id))

            except:

                pass

        if valid_ids:

            placeholders = ",".join(
                ["?"] * len(valid_ids)
            )

            products = conn.execute(
                f"""
                SELECT *
                FROM products
                WHERE id IN ({placeholders})
                """,
                valid_ids
            ).fetchall()

        conn.close()

    for product in products:

        total += float(product["price"])

    # -----------------------------------------------------
    # PLACE ORDER
    # -----------------------------------------------------

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")

        if not name or not email or not phone or not address:

            flash("Please fill all checkout details.")

            return redirect(url_for("checkout"))

        # Clear cart after order
        session["cart"] = []

        session.modified = True

        return redirect(url_for("success"))

    return render_template(
        "checkout.html",
        products=products,
        total=total,
        cart_count=len(cart_ids)
    )


# =========================================================
# SUCCESS
# =========================================================

@app.route("/success")
def success():

    return render_template("success.html")


# =========================================================
# ABOUT
# =========================================================

@app.route("/about")
def about():

    return render_template("about.html")


# =========================================================
# BLOG
# =========================================================

@app.route("/blog")
def blog():

    return render_template("blog.html")


# =========================================================
# BLOG POST
# =========================================================

@app.route("/blog/<int:post_id>")
def blog_post(post_id):

    return render_template(
        "blog_post.html",
        post_id=post_id
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:

            flash("Please enter email and password.")

            return redirect(url_for("home"))

        session["user"] = email

        return redirect(url_for("home"))

    return redirect(url_for("home"))


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect(url_for("home"))


# =========================================================
# SEARCH PRODUCTS
# =========================================================

@app.route("/search")
def search():

    search_text = request.args.get("q", "")

    conn = get_db()

    products = conn.execute("""
        SELECT *
        FROM products
        WHERE name LIKE ?
        OR description LIKE ?
        ORDER BY id DESC
    """, (
        "%" + search_text + "%",
        "%" + search_text + "%"
    )).fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=products,
        search_text=search_text,
        cart_count=len(session.get("cart", []))
    )


# =========================================================
# ERROR HANDLER - 404
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>
    <p>The page you are looking for does not exist.</p>
    <a href="/">Go Home</a>
    """, 404


# =========================================================
# ERROR HANDLER - 500
# =========================================================

@app.errorhandler(500)
def internal_error(error):

    return """
    <h1>500 - Internal Server Error</h1>
    <p>Something went wrong.</p>
    <a href="/">Go Home</a>
    """, 500


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )