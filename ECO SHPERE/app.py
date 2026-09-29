from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB = Path("store.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        image TEXT NOT NULL,
        category TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS blog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        email TEXT NOT NULL,
        address TEXT NOT NULL,
        total REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        products = [
            ("Smart Watch X1", "Fitness tracking, notifications and modern design.", 2499, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800", "Electronics"),
            ("Wireless Headphones", "Comfortable headphones with rich sound.", 1799, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800", "Electronics"),
            ("Running Shoes", "Lightweight everyday running shoes.", 2199, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800", "Fashion"),
            ("Backpack Pro", "Durable backpack for college and travel.", 1299, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800", "Accessories"),
            ("Sunglasses Classic", "Simple stylish sunglasses for daily use.", 899, "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=800", "Fashion"),
            ("Coffee Mug", "Minimal ceramic mug for home or office.", 399, "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=800", "Home")
        ]
        conn.executemany(
            "INSERT INTO products(name,description,price,image,category) VALUES(?,?,?,?,?)",
            products
        )

    if conn.execute("SELECT COUNT(*) FROM blog").fetchone()[0] == 0:
        posts = [
            ("How to Choose the Right Product Online",
             "Online shopping becomes easier when you compare features, price, reviews and warranty before buying. Make a short checklist and choose a product that matches your actual needs.",
             "Admin", "2026-09-20"),
            ("5 Simple Tips for Smart Shopping",
             "Set a budget, compare products, read specifications, check return policies and avoid buying only because of a discount. Smart shopping is about value, not just the lowest price.",
             "Admin", "2026-09-22"),
            ("Why a Good E-commerce Website Matters",
             "A useful e-commerce website should be easy to navigate, fast, mobile-friendly and clear about product information. A simple checkout experience can make shopping much easier.",
             "Admin", "2026-09-25")
        ]
        conn.executemany(
            "INSERT INTO blog(title,content,author,created_at) VALUES(?,?,?,?)",
            posts
        )
    conn.commit()
    conn.close()

@app.route("/")
def home():
    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    posts = conn.execute("SELECT * FROM blog ORDER BY id DESC LIMIT 3").fetchall()
    conn.close()
    return render_template("index.html", products=products, posts=posts)

@app.route("/products")
def products():
    category = request.args.get("category", "")
    conn = get_db()
    if category:
        items = conn.execute("SELECT * FROM products WHERE category=? ORDER BY id DESC", (category,)).fetchall()
    else:
        items = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("products.html", products=items, category=category)

@app.route("/product/<int:product_id>")
def product(product_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    conn.close()
    if not item:
        return "Product not found", 404
    return render_template("product.html", product=item)

@app.route("/add-to-cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    cart = session.get("cart", {})
    key = str(product_id)
    cart[key] = cart.get(key, 0) + 1
    session["cart"] = cart
    flash("Product added to cart!")
    return redirect(request.referrer or url_for("products"))

@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    items = []
    total = 0
    conn = get_db()
    for pid, qty in cart.items():
        item = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if item:
            subtotal = item["price"] * qty
            items.append({"product": item, "qty": qty, "subtotal": subtotal})
            total += subtotal
    conn.close()
    return render_template("cart.html", items=items, total=total)

@app.route("/remove-from-cart/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = session.get("cart", {})
    if not cart:
        return redirect(url_for("cart"))

    conn = get_db()
    items, total = [], 0
    for pid, qty in cart.items():
        item = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if item:
            subtotal = item["price"] * qty
            items.append({"product": item, "qty": qty, "subtotal": subtotal})
            total += subtotal

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        address = request.form["address"].strip()
        if not name or not email or not address:
            flash("Please fill all fields.")
            conn.close()
            return redirect(url_for("checkout"))

        conn.execute(
            "INSERT INTO orders(customer_name,email,address,total) VALUES(?,?,?,?)",
            (name, email, address, total)
        )
        conn.commit()
        conn.close()
        session["cart"] = {}
        return render_template("success.html", name=name, total=total)

    conn.close()
    return render_template("checkout.html", items=items, total=total)

@app.route("/blog")
def blog():
    conn = get_db()
    posts = conn.execute("SELECT * FROM blog ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("blog.html", posts=posts)

@app.route("/blog/<int:post_id>")
def blog_post(post_id):
    conn = get_db()
    post = conn.execute("SELECT * FROM blog WHERE id=?", (post_id,)).fetchone()
    conn.close()
    if not post:
        return "Blog post not found", 404
    return render_template("blog_post.html", post=post)

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
