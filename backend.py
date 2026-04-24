# Importing every function from flask we needed to manage our backend code, starting with...
# render_template = Simply rendering the templates for each specifc web page
# redirect & url_for  = Redirecting the user to different web pages using url_for to decide where the user will end up in(PARAMOUNT for authentication logic)
# request = requesting different diffrent variables outside the backend code(e.g. forms & args) & withing(e.g. method). Ultimatly requetsiing functions and data that the backend will utalise
# flash =  Simple use of flashing messages during key aspects of theusers journey of our wep app(Jakob Nielsen 1994: Visibility of System Status)
# session = Use of putting a user in a session that will be saved unless a certain action is done(e.g. loggin out of account) Main use of holding data untilm outputted
from email import message
import re
from flask import Flask, render_template, redirect, url_for, request, flash, session
# Importing timedelta to decide how long sessions last. 
from datetime import timedelta, date
# Importing SQLAlchmy for database Creation / Management
from flask_sqlalchemy import SQLAlchemy
# Importing hashing to hash password for any later data breaches
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
# Adding seceret key for security purposes ~ MUST for web app to run
app.secret_key = "key"
# Database location (creating a file named GLH.db in my project folder which i can open in DB Browser)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///GLH.database'

# Simple quality of life fix to turn off a feature that uses extra memory/resources
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setting the time duration using time module mentioned priorly
app.permanent_session_lifetime = timedelta(hours=2)

db = SQLAlchemy(app)

# List of database tables with Primary Keys, Foreign Keys & Attributes inside them.

# Some Attributes havingncertain rules for logic purposes e.g... 
# unique = attribite variable must be unique/solely(great example being in the User table having user_email be unique so no more that one email addresses can have more than 1 account)
# Nullable= Simply setting a rule that a attribute variable must be entered or not(great example bring password_hash, password MUST be entered for a user the login. Some attrbites haive infomation that isnt really necessary for our database so they can be left empty)
# Default = Simply setting the value of an attribute unless changed through an algorith along the digital solution

# Data Type = Setting the data type of the attrbute simply for simple clarification

# MAJOR OVERHAUL compared to proposal for logic purposes

# --- 1. USER TABLE --- Including The User primary key(user_id) and attrbitues.
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(20), default="customer") 
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    user_address = db.Column(db.String(255))
    user_email = db.Column(db.String(255), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(128), nullable=False) 
    loyalty_scheme = db.Column(db.Boolean(), default=False, nullable=False)
    
    # Relationship to find all orders for a user
    orders = db.relationship('Order', backref='customer', lazy=True)

# --- 2. ORDER TABLE (The "Receipt" Header) --- Including The Order primary key(order_id), foreign key(user_id) and attrbitues.
class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    # MAYBE order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    ship_date = db.Column(db.Date)
    ship_charge = db.Column(db.Numeric(10, 2), default=0.00)
    
    # FK: Link to the User who placed the order
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
    
    # Relationship to find all items inside this specific order
    items = db.relationship('Product', backref='parent_order', lazy=True)

# --- 3. STOCK TABLE (The "Master Menu") --- Including The Stock primary key(stock_id), foreign key(warehouse_id & producer_id) and attrbitues.
class Stock(db.Model):
    __tablename__ = 'stock'
    stock_id = db.Column(db.Integer, primary_key=True)
    stock_name = db.Column(db.String(100), nullable=False)
    stock_price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_description = db.Column(db.Text)
    stock_level = db.Column(db.Integer, default=0)
    is_vegetarian = db.Column(db.Boolean(), default=False, nullable=False)
    allergy_tag = db.Column(db.String(50), nullable=True)

    # FK: Where the stock is made and who made the stock
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.warehouse_id'))
    producer_id = db.Column(db.Integer, db.ForeignKey('producer.producer_id'))

# --- 4. PRODUCT TABLE (The "Order Line Items") --- Including The Product primary key(product_id), foreign key(order_id & stock_id) and attrbitues.
class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    
    # FK: Link to the specific Menu Item (Stock) and the Order (Receipt)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.stock_id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'), nullable=False)
    
    product_quantity = db.Column(db.Integer, nullable=False, default=1)
    
    # Pricing logic
    total_price = db.Column(db.Numeric(10, 2))      # qty * stock_price
    discount_amount = db.Column(db.Numeric(10, 2), default=0.00) 
    discount_price = db.Column(db.Numeric(10, 2))   # total_price - discount_amount

# --- 5. WAREHOUSE & PRODUCERS (Supply Chain) --- Including The Warehouse & Producer primary key(warehouse_id & producer_id) and attrbitues.
class Warehouse(db.Model):
    warehouse_id = db.Column(db.Integer, primary_key=True)
    warehouse_name = db.Column(db.String(100), nullable=False)
    warehouse_location = db.Column(db.String(255), nullable=False)
    stocks = db.relationship('Stock', backref='location', lazy=True)

class Producer(db.Model):
    producer_id = db.Column(db.Integer, primary_key=True)
    producer_name = db.Column(db.String(100), nullable=False)
    stocks = db.relationship('Stock', backref='supplier', lazy=True)

class Contact(db.Model):
    contact_id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255))
    phonenumber = db.Column(db.String(20))




# The route of the home page of GLH digital solution using both / & /home. / to signify this is the index(beginning page) & home for transparency and redirection
@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")
         

# The route for registering an account with GLH. using both GET & POST METHOD
@app.route('/register', methods=["GET", "POST"])
def register():
    #Requesting post since email & password are both sensitive variables~ Secutiry Purposes
    if request.method == "POST":
        # Making the session permanent
        session.permanent = True
        # Requesting both email & password from the form in "register.html"
        email = request.form["email"]
        password = request.form["password"]
        firstname = request.form["first_name"]
        lastname = request.form["last_name"]
        phonenumber = request.form["phone_number"]
        address = request.form["address"]



        # Using the hashing function generate_password_hash to hash the priorply users password~ ~ Secutiry Purposes
        hashed_password = generate_password_hash(password)

        # Turing user inputted variables into attributes of the User table, thus creating a new user. also signifying they are a customer.
        new_user = User(user_email=email, password_hash = hashed_password,first_name=firstname, last_name=lastname, phone_number=phonenumber, user_address=address, user_type="customer")
        # Firstly adding the new_user into the database then actually commiting it
        db.session.add(new_user)
        db.session.commit()

        # Use of message flashing to inform the user of their progress.
        flash("You have successfully registered an account! Please try logging in to it!")
        # Once register the user will be redirected the the login page so they can now log in
        return redirect(url_for("login"))
    else:
        # Merely redndering the "register.html" page
        return render_template("register.html")


# The route for the login system, pulling POSTING the infomation and using SQL to find the specific account details
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session.permanent = True
        email = request.form["email"]
        password = request.form["password"]

        # Filtering the user_email column to find the exact say email as the one inputted
        user = User.query.filter_by(user_email=email).first()

        # IF Both the user & password are found in the same column 
        if user and check_password_hash(user.password_hash, password):
            #Turn all variable/functions needed into sessions
            session["user_id"] = user.user_id
            session["user_type"] = user.user_type
            session["basket"] = []
            session["loyalty"] = user.loyalty_scheme

            # If the user_type is admin FLASH a specific admin welcome message whilst redirecting the admin to the admin page
            if user.user_type  == "admin":
                flash("Welcome administrator!")
                return redirect(url_for("admin"))
            else:
                # If they are not(if not admin they can only be a customer) FLASH a specific user welcome message whilst redirecting the user to the menu page
                if session["user_id"]:
                    loyalty_scheme = True
                flash(f"Welcome {email}!")
                return redirect(url_for("menu"))
    else:
        return render_template("login.html")


@app.route('/logout')
# Logout function that simply clears all session data the flashing message of user progress then ultimatley redirceting the user to the login page
def logout():
    session.clear()
    flash("You have been successfully logged out.")
    return redirect(url_for("login"))

# Menu route for simply displaying menu items including both allergy & vegetarian filters
@app.route('/menu')
def menu():
    #Requesting args for both my filters
    allergy = request.args.get("allergy")
    vegetarian = request.args.get("vegetarian")
    
    # Algorithm that checks if the url parameter include a exclusion pf either a allergy(e.g. Dairy) or if its vegetarian. if their are no exclusion all items will be shown
    if allergy:
        items = Stock.query.filter(~Stock.allergy_tag.contains(allergy)).all()
    elif vegetarian:
        items = Stock.query.filter(~Stock.is_vegetarian.contains(vegetarian)).all()
    else:
        items = Stock.query.all()
    # After algorithm the items filtered or not and now stored as products in the "menu.html"
    return render_template("menu.html", products=items)


# Route to add products(items) to basket
@app.route('/add_to_basket/<int:sid>')
def add_to_basket(sid):
    # Initialize basket as a list if it doesn't exist
    if "basket" not in session:
        session["basket"] = []

    # Querying for the SPECIFIC item using the ID
    item = Stock.query.get(sid)

    if item and item.stock_level > 0:
        # Get the list, updates it, then re-saves it
        basket = session["basket"]
        basket.append(sid)  # Storing the stock ID only
        session["basket"] = basket # Turning basket back withing a session
        
        # Flashing the message that a stock itemn has been added to basket, when their is no stock another flashed message inforoming the user will be sent. Finally redirecting the user to the user page back.
        flash(f"{item.stock_name} added to basket")
        flash(f"Current basket list: {basket}")
    else:
        flash(f"Current basket list: {basket}")
        flash("Item out of stock or not found")

    return redirect(url_for("menu"))


# Route to remove products(items) to basket
@app.route('/remove_from_basket/<int:sid>')
def remove_from_basket(sid):
    # Algorithm to check if both the basket and the stock_id are in session
    if "basket" in session and sid in session["basket"]:
        session["basket"].remove(sid)
        session.modified = True
        flash("Item has been removed from basket")
    return redirect(url_for("menu"))

# sid is stock id
@app.route('/checkout')
def checkout():
    # 1. Get the basket or an empty list if it's missing 2. Storing the subtotal with no numeric value 3. having the display_items as an empty list
    basket_ids = session.get("basket", [])    
    subtotal = 0
    display_items = []

    # . Looping through the IDs in the session
    for sid in basket_ids:
        # Querying for the SPECIFIC item using the ID
        item = Stock.query.get(sid)
        # Filtering the specific IDs product financial variables(e.g. total_price)
        
        if item: # If item exists, total price of specifc will be added to the subtotal and the appended as a displayed item on our menu
            subtotal += float(item.stock_price)
            display_items.append(item)
    #Loyalty Logic if the user is logged in they recievce a 5% discount on their purchase. plus the aritmetic needed to make this possible
    loyalty_discount = 0.00
    if "user_id" in session:
        loyalty_discount = subtotal * 0.05
    discounted_subtotal = subtotal - loyalty_discount


    # Providing the aquiring of order solution as GLH asked for, the user will be given a choice of delivery or collecetion, plus the aritmetic needed to make this possible
    method = request.args.get("method", "collection")
    shipping_fee = 2.50 if method == "delivery" else 0.00

    #Totalling up every key value at once
    grand_total = discounted_subtotal + shipping_fee

    # Passing all needed variables
    return render_template("checkout.html",
    items=display_items,
    subtotal=subtotal,
    discount=loyalty_discount, 
    total=grand_total, 
    shipping=shipping_fee, 
    method=method)

# Place Order Route is used to remove remove the applicable stock when a order is placed and puts the order infomation securely in our database
@app.route("/place_order")
def place_order():
    basket_ids = session.get("basket", [])
    if not basket_ids:
        # If a user tries to place a order with a empty basket the system flashes them a message informing them to add a item to basket
        flash("Your basket is currently empty! Please add you desired products to basket")
        return redirect(url_for("menu"))

    new_order = Order(user_id = session.get("user_id"), order_date=date.today())
    db.session.add(new_order)

    # The algorith removing the stock_level corrospoding the the baskey value when a order is being placed
    for sid in basket_ids:
        item = Stock.query.get(sid)
        if item and item.stock_level > 0:
            item.stock_level = item.stock_level - 1
        else: 
            flash(f"{item.stock_name} has ran out of stock")
            return redirect(url_for("checkout"))
        
    db.session.commit()
    session["basket"] = []
    flash("Order placed successfully!")

    # THIS LINE MUST BE HERE - Outside the loop and the if/else
    return redirect(url_for("home"))


@app.route('/admin')
def admin():
    # We check the session, not the 'user' variable (which only exists in login)
    if session.get("user_type") == "admin":
        stock=Stock.query.all()
        return render_template("admin.html", stock=stock)
    else:
        # Returns a simple message and the 403 (Forbidden)
        return "Access Denied! Admins Only. If you have admin privaleges Please Log In", 403

# Route for updating stock in the admin dashboard
@app.route('/update_stock/<int:sid>', methods=["POST"])
def update_stock(sid):
    if session.get("user_type") != "admin":
        # Reroutes the user back to the login page if the user in the current session isnt a admin
        return redirect(url_for("login"))
    else: 
        item = Stock.query.get(sid)
        # Gets the new numeric value of the admin inputted stock level then commits it to the database. A seamless transition of data movement
        item.stock_level = request.form.get("new_stock")
        db.session.commit()
        # Flashes message directly on the admin page updating the administrator that the stock has been updated
        flash(f"{item.stock_name} has been updated")
        return redirect(url_for("admin"))

    
@app.route('/about')
def about():
    return render_template("about.html")

# The route for the contact system, pulling POSTING the customer/admin message to use securely. This is needed for Business to Consumer communication
@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        message = request.form["message"]
        email = request.form["email"]
        phonenumber = request.form["phonenumber"]



        new_message = Contact(message=message, email=email, phonenumber=phonenumber)

        db.session.add(new_message)
        db.session.commit()
        flash("Your enquiry has successfully been dent to us!")
        return redirect(url_for("home"))
    else:
        return render_template("contact.html")


# Data Base Seeding
def seed_db():
    with app.app_context():
        db.create_all()

        # Check for the admins logins & hasing admin password~ Security purposes. Finally adding admin to session
        if not User.query.filter_by(user_email="glh@admin.com").first():
            hashed_admin = generate_password_hash("Greenfield")
            admin = User(user_email="glh@admin.com", password_hash=hashed_admin, user_type="admin")
            db.session.add(admin)

        if not User.query.filter_by(user_email="A1@admin.com").first():
            hashed_admin1 = generate_password_hash("123")
            admin1 = User(user_email="A1@admin.com", password_hash=hashed_admin1, user_type="admin")
            db.session.add(admin1)

        if not User.query.filter_by(user_email="Valley@admin.com").first():
            hashed_admin2 = generate_password_hash("456")
            admin2 = User(user_email="Valley@admin.com", password_hash=hashed_admin2, user_type="admin")
            db.session.add(admin2)

        if not User.query.filter_by(user_email="Core@admin.com").first():
            hashed_admin3 = generate_password_hash("789")
            admin3 = User(user_email="Core@admin.com", password_hash=hashed_admin3, user_type="admin")
            db.session.add(admin3)

            db.session.commit()

            # Get or Create Warehouse & Producer
            wr = Warehouse.query.filter_by(warehouse_name="GLH Warehouse").first()

            # If warehouse do not exist simply add them           
            if not wr:
                wr = Warehouse(warehouse_name="GLH Warehouse", warehouse_location="LocationCarti")
                db.session.add(wr)
            
            pr1 = Producer.query.filter_by(producer_name="A1 Food Group").first()
            pr2 = Producer.query.filter_by(producer_name="Valley Goods").first()
            pr3 = Producer.query.filter_by(producer_name="Core Cuisine").first()

            # If specifc producers do not exist simply add them
            if not pr1:
                pr1 = Producer(producer_name="A1 Food Group")
                db.session.add(pr1)
            if not pr2:
                pr2 = Producer(producer_name="Valley Goods")
                db.session.add(pr2)
            if not pr3:
                pr3 = Producer(producer_name="Core Cuisine")
                db.session.add(pr3)

            # Commit here so the IDs (wr.warehouse_id, pr.producer_id) are generated
            db.session.commit()


            # Defining all products including their infomation(e.g. stock_price)
            s1 = Stock(stock_name="Margherita Pizza", 
                       stock_price=11.50, stock_description="Classic tomato, mozzarella, and basil", stock_level=0, 
                       is_vegetarian=True, allergy_tag="Dairy, Gluten", 
                       warehouse_id=wr.warehouse_id, producer_id=pr1.producer_id)
            s2 = Stock(stock_name="Spicy Pepperoni Pizza",
                      stock_price=13.00, stock_description="Double pepperoni with hot honey drizzle", stock_level=1, 
                      is_vegetarian=False, allergy_tag="Dairy, Gluten", 
                      warehouse_id=wr.warehouse_id, producer_id=pr2.producer_id)

            s3 = Stock(stock_name="Garden Salad", 
                       stock_price=8.50, stock_description="Mixed greens with balsamic vinaigrette", stock_level=40, 
                       is_vegetarian=True, allergy_tag="None", 
                       warehouse_id=wr.warehouse_id, producer_id=pr1.producer_id)

            s4 = Stock(stock_name="Garlic Prawn Pasta", stock_price=18.00, stock_description="Linguine with king prawns and chili", stock_level=12, 
                       is_vegetarian=False, allergy_tag="Gluten", 
                       warehouse_id=wr.warehouse_id, producer_id=pr2.producer_id)

            s5 = Stock(stock_name="Satay Chicken Skewers", stock_price=7.50, stock_description="Grilled chicken with peanut sauce", stock_level=15
                       , is_vegetarian=False, allergy_tag="Peanuts", 
                       warehouse_id=wr.warehouse_id, producer_id=pr3.producer_id)

            s6 = Stock(stock_name="French Fries", stock_price=5.50, stock_description="Crispy fries prepared seasoning", stock_level=50
                       , is_vegetarian=True, allergy_tag="Dairy", 
                       warehouse_id=wr.warehouse_id, producer_id=pr2.producer_id)

            s7 = Stock(stock_name="Classic Burger", stock_price=12.50, stock_description="Beef patty, cheddar, and secret sauce", stock_level=22, 
                       is_vegetarian=False, allergy_tag="Dairy, Gluten", 
                       warehouse_id=wr.warehouse_id, producer_id=pr1.producer_id)

            s8 = Stock(stock_name="Chocolate Brownie", stock_price=6.50, stock_description="Warm fudge brownie with vanilla ice cream", stock_level=20, 
                       is_vegetarian=False, allergy_tag="Egg, Dairy, Gluten", 
                       warehouse_id=wr.warehouse_id, producer_id=pr3.producer_id)

            s9 = Stock(stock_name="Almond Croissant", stock_price=3.50, stock_description="Flaky pastry with frangipane filling", stock_level=12, 
                       is_vegetarian=False, allergy_tag="Nuts, Gluten", 
                       warehouse_id=wr.warehouse_id, producer_id=pr2.producer_id)

            s10 = Stock(stock_name="Water", stock_price=0.70, stock_description="500ml bottled spring water", stock_level=100
                        , is_vegetarian=True, allergy_tag="None", 
                        warehouse_id=wr.warehouse_id, producer_id=pr1.producer_id)

            s11 = Stock(stock_name="Cola", stock_price=1.25, stock_description="330ml classic cola can", stock_level=48, 
                        is_vegetarian=True, allergy_tag="None", 
                        warehouse_id=wr.warehouse_id, producer_id=pr3.producer_id) 
            
            s12 = Stock(stock_name="Sprite", stock_price=1.25, stock_description="330ml classic sprite can", stock_level=36, 
                        is_vegetarian=True, allergy_tag="None", 
                        warehouse_id=wr.warehouse_id, producer_id=pr2.producer_id)

            s13 = Stock(stock_name="Apple Juice", stock_price=2.00, stock_description="1L Carton of Apple Juice", 
                        stock_level=36, is_vegetarian=True, allergy_tag="None", 
                        warehouse_id=wr.warehouse_id, producer_id=pr1.producer_id)

            s14 = Stock(stock_name="Orange Juice", stock_price=2.00, stock_description="1L Carton of Orange Juice", stock_level=24, 
                        is_vegetarian=True, allergy_tag="None", 
                        warehouse_id=wr.warehouse_id, producer_id=pr3.producer_id)

            s15 = Stock(stock_name="Milk", stock_price=2.90, stock_description="3L Carton of Semi-Skimmed Milk", stock_level=15, 
                        is_vegetarian=True, allergy_tag="Dairy", 
                        warehouse_id=wr.warehouse_id, producer_id=pr1.producer_id)

            # Holding all items as a list then ultimatley commiting them to the databse.
            items = ([s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15])
            db.session.add_all(items)
            db.session.commit()
            print("GLH Database securely seeded successfully!")

if __name__ == '__main__':
    # Seedind Database before the web app runs
    seed_db()
    app.run(debug=True)
