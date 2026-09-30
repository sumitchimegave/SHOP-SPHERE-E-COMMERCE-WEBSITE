from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)

# ---------------------------------------------------------
# APP CONFIGURATION
# ---------------------------------------------------------

app.secret_key = "studyhub-secret-key-change-this-later"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database", "studyhub.db")


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.route("/")
def home():
    conn = get_db()

    products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC LIMIT 6"
    ).fetchall()

    conn.close()

    return render_template(
        "home.html",
        products=products
    )


# ---------------------------------------------------------
# RESOURCES / ALL PRODUCTS
# ---------------------------------------------------------

@app.route("/resources")
def resources():
    conn = get_db()

    products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=products
    )


# ---------------------------------------------------------
# PRODUCTS
# ---------------------------------------------------------

@app.route("/products")
def products():
    conn = get_db()

    products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=products
    )


# ---------------------------------------------------------
# SINGLE PRODUCT
# ---------------------------------------------------------

@app.route("/product/<int:product_id>")
def product(product_id):

    conn = get_db()

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    conn.close()

    if product is None:
        return "Product not found", 404

    return render_template(
        "product.html",
        product=product
    )


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.")
            return render_template("login.html")

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
            """,
            (email, password)
        ).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            flash("Login successful!")

            return redirect(url_for("home"))

        flash("Invalid email or password.")

    return render_template("login.html")


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:

            flash("Please fill in all fields.")

            return render_template("register.html")

        conn = get_db()

        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_user:

            conn.close()

            flash("An account with this email already exists.")

            return render_template("register.html")

        conn.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (name, email, password)
        )

        conn.commit()
        conn.close()

        flash("Registration successful. Please login.")

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("home"))


# ---------------------------------------------------------
# CART
# ---------------------------------------------------------

@app.route("/cart")
def cart():

    cart_items = session.get("cart", [])

    conn = get_db()

    products = []

    for product_id in cart_items:

        product = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        if product:
            products.append(product)

    conn.close()

    total = 0

    for item in products:
        total += item["price"]

    return render_template(
        "cart.html",
        products=products,
        total=total
    )


# ---------------------------------------------------------
# ADD TO CART
# ---------------------------------------------------------

@app.route("/add-to-cart/<int:product_id>", methods=["POST", "GET"])
def add_to_cart(product_id):

    cart = session.get("cart", [])

    cart.append(product_id)

    session["cart"] = cart

    flash("Product added to cart.")

    return redirect(url_for("cart"))


# ---------------------------------------------------------
# REMOVE FROM CART
# ---------------------------------------------------------

@app.route("/remove-from-cart/<int:product_id>")
def remove_from_cart(product_id):

    cart = session.get("cart", [])

    if product_id in cart:
        cart.remove(product_id)

    session["cart"] = cart

    return redirect(url_for("cart"))


# ---------------------------------------------------------
# CHECKOUT
# ---------------------------------------------------------

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    cart = session.get("cart", [])

    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for("resources"))

    conn = get_db()

    products = []

    for product_id in cart:

        product = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        if product:
            products.append(product)

    conn.close()

    total = sum(item["price"] for item in products)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()

        if not name or not email or not address:

            flash("Please fill in all checkout details.")

            return render_template(
                "checkout.html",
                products=products,
                total=total
            )

        conn = get_db()

        cursor = conn.execute(
            """
            INSERT INTO orders
            (customer_name, customer_email, address, total)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, address, total)
        )

        order_id = cursor.lastrowid

        conn.commit()
        conn.close()

        session["cart"] = []

        return redirect(
            url_for(
                "success",
                order_id=order_id
            )
        )

    return render_template(
        "checkout.html",
        products=products,
        total=total
    )


# ---------------------------------------------------------
# ORDER SUCCESS
# ---------------------------------------------------------

@app.route("/success")
def success():

    order_id = request.args.get("order_id")

    return render_template(
        "success.html",
        order_id=order_id
    )


# ---------------------------------------------------------
# ORDERS
# ---------------------------------------------------------

@app.route("/orders")
def orders():

    conn = get_db()

    orders = conn.execute(
        "SELECT * FROM orders ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "orders.html",
        orders=orders
    )


# ---------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )