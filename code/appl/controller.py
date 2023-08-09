from flask import render_template 
from flask import request
from flask import redirect
from flask import session 
from flask import current_app as app
from appl.database import db
from appl.dbmodels import User 
from appl.dbmodels import Product 
from appl.dbmodels import Purchases
from passlib.hash import pbkdf2_sha256 as passhash
import json

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        products = Product.query.all()
        if "user" in session:
            return render_template("landing.html", user = session["user"], signed=True, products = products)
        else:
            return render_template("landing.html", user = "", signed=False, products = products)
    else:
        product_id, count = request.form["product"], request.form["count"]
        product = Product.query.filter_by(id = product_id).first()
        
        cart = json.loads(session["cart"])
        if product_id in cart:
            current = int(count) + int(cart[product_id])
            if current <= int(product.units):
                cart[product_id] = str(int(cart[product_id]) + int(count))
        else:
            current = int(count)
            if current <= int(product.units):
                cart[product_id] = count

        session["cart"] = json.dumps(cart)
        print(session["cart"])
        return redirect("/")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    elif request.method == "POST":
        username = request.form["username"]
        email=request.form["email"]
        telephone=request.form["telephone"]
        address=request.form["address"]
        dob=request.form["dob"]
        password = request.form["password"]
        password = passhash.hash(password)
        user = User.query.filter_by(name = username).first()        
        if user is not None:
            return redirect("/login")
        user = User(name = username, 
                    password = password,
                    email=email,
                    telephone=telephone,
                    address=address,
                    dob=dob)
        db.session.add(user)
        db.session.commit()
        session["user"] = username
        session["cart"] = json.dumps(dict())
        return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(name = username).first()
        if user is None:
            return redirect("/signup")
        if not passhash.verify(password, user.password):
            return redirect("/login")
        session["user"] = username
        session["cart"] = json.dumps(dict())
        return redirect("/")

@app.route("/logout")
def logout():
    if "user" in session:
        session.pop("user")
        session.pop("cart")
    return redirect("/")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/dashboard")
def dashboard():
    if "user" in session:
        user = User.query.filter_by(name=session["user"]).first()
        if user.admin:
            products = Product.query.all()
            return render_template("Admin_dashboard.html", products = products)
    return redirect("/")

@app.route("/add_product", methods = ["GET", "POST"])
def add_product():
    if "user" in session:
        user = User.query.filter_by(name=session["user"]).first()
        if user.admin:
            if request.method == "GET":
                return render_template("Add_products.html")
            elif request.method == "POST":
                name = request.form["name"]
                description = request.form["description"]
                units = request.form["units"]
                price = request.form["price"]
                img = request.files["img"]
                shelf_life=request.form["shelf_life"]
                manufacturer_details=request.form["manufacturer_details"]
                fsaai_license=request.form["fsaai_license"]
                disclaimer=request.form["disclaimer"]
                category_n=request.form["category_n"]
                category_id = request.form["category_id"]
                product = Product(name = name,description = description, 
                                 units = units,owner = user.id,
                                 price = price,shelf_life =shelf_life,
                                 manufacturer_details=manufacturer_details,fsaai_license=fsaai_license,
                                 disclaimer=disclaimer,category_n=category_n,category_id= category_id)
                db.session.add(product)
                db.session.commit()
                img.save("./code/static/products/" + str(product.id) + ".png")
                return redirect("/dashboard")
    return redirect("/")


@app.route("/delete_product/<product_id>", methods = ["GET", "POST"])
def delete_product(product_id):
    if "user" in session:
        user = User.query.filter_by(name=session["user"]).first()
        if user.admin:
            if request.method == "GET":
                return render_template("delete_products.html")
            elif request.method == "POST":
                if "yes" in request.form:
                    product = Product.query.filter_by(id = product_id).first()
                    db.session.delete(product)
                    db.session.commit()
                    return redirect("/dashboard")
                else:
                    return redirect("/dashboard")
    return redirect("/")

@app.route("/edit_product/<product_id>", methods = ["GET", "POST"])
def edit_product(product_id):
    if "user" in session:
        user = User.query.filter_by(name=session["user"]).first()
        if user.admin:
            product = Product.query.filter_by(id = product_id).first()
            if request.method == "GET":
                return render_template("editing_products.html", product=product)
            elif request.method == "POST":
                name = request.form["name"]
                description = request.form.get("description", None)
                units = request.form.get("units", None)
                price = request.form.get("price", None)
                shelf_life=request.form["shelf_life"]
                manufacturer_details=request.form["manufacturer_details"]
                fsaai_license=request.form["fsaai_license"]
                disclaimer=request.form["disclaimer"]
                category_n=request.form["category_n"]
                category_id = request.form["category_id"]
                img = request.files.get("img", None)
                if name:
                    product.name = name
                if description:
                    product.description = description
                if units:
                    product.units = units
                if price:
                    product.price = price
                if shelf_life:
                    product.shelf_life
                if manufacturer_details:
                    product.manufacturer_details
                if fsaai_license:
                    product.fsaai_license
                if disclaimer:
                    product.disclaimer
                if category_n:
                    product.category_n
                if category_id :
                    product.category_id 
                db.session.commit()
                if img:
                    img.save("./static/products/" + str(product.id) + ".png")
                return redirect("/dashboard")
    return redirect("/")

@app.route("/cart", methods = ["GET", "POST"])
def cart():
    if "user" in session:
        cart = json.loads(session["cart"])
        user = User.query.filter_by(name=session["user"]).first()
        products = [[Product.query.filter_by(id = product_id).first(), cart[product_id]] for product_id in cart.keys()]
        total = sum([int(Product.query.filter_by(id = product_id).first().price) * int(cart[product_id]) for product_id in cart.keys()])
        if request.method == "GET":
            return render_template("cart.html", products = products, total = total)
        else:
            if "remove" in request.form:
                cart.pop(request.form["remove"])
                session["cart"] = json.dumps(cart)
                return redirect("/cart")
            else:
                for product, count in products:
                    product.units -= int(count)
                    purchase = Purchases(product=product.id, owner=product.owner, customer=user.id, count=count)
                    db.session.add(purchase)
                    db.session.commit()
                session["cart"] = json.dumps(dict())
                return redirect("/checkout")
    return redirect("/")

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin.html")
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(name = username).first()
        if user is None:
            return redirect("/signup")
        if not passhash.verify(password, user.password):
            return redirect("/admin_login")
        session["user"] = username
        session["cart"] = json.dumps(dict())
        return redirect("/")



