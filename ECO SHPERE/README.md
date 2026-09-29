# ShopSphere E-commerce Website

## Technology
- Frontend: HTML5, CSS3, Jinja templates
- Backend: Python Flask
- Database: SQLite
- Blog: SQLite-backed blog pages
- Cart: Flask session

## Run in VS Code / Windows

1. Install Python.
2. Open this folder in VS Code.
3. Open Terminal > New Terminal.
4. Create a virtual environment:
   `python -m venv venv`
5. Activate it:
   `venv\Scripts\activate`
6. Install Flask:
   `pip install -r requirements.txt`
7. Start the website:
   `python app.py`
8. Open the local address shown in the terminal, normally:
   `http://127.0.0.1:5000`

The `store.db` database is automatically created the first time the app starts.

## Main features
- Home page
- Product listing
- Product details
- Category filter
- Add/remove cart
- Checkout and order storage
- Blog listing and article pages
- About page
- Responsive CSS
