from cs50 import SQL
from flask import Flask, url_for, render_template, request, session, redirect

# Flask will use directory of app.py to search for templates and static
app = Flask(__name__)

# Set the secret key so users will not be able to change session cookie information
app.secret_key = "af3c081ff9e7c80f132f848ea44f0a1fd89cf5388a517edbe268dcb3d9f57c9a"

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///app.db")


# Function to add Tables or Categories to SQL
def addTableToSQL(table, category):
    if len(db.execute("SELECT main_table FROM userTables WHERE user_id = 522 AND main_table = ?", table)) == 0:
        print("Dictionary is empty. Creating new table")
        db.execute("INSERT INTO userTables (user_id, main_table, category) VALUES (522, ?, ?)", table, category)
    else:
        print("Dictionary exists")
        if len(db.execute("SELECT main_table FROM userTables WHERE user_id = 522 AND category = ?", category)) == 0:
            db.execute("INSERT INTO userTables (user_id, main_table, category) VALUES (522, ?, ?)", table, category)
            print("Inserted new category into table")
        else:
            print("Such category already exists")


# Function to read all tables belonging to user's id
def readTables(id):
    userTables = db.execute("SELECT DISTINCT main_table FROM userTables WHERE user_id = ? ORDER BY main_table ASC", id)
    print(userTables[0]["main_table"])
    return userTables


# Function to read categories from passed tables belonging to user's id
def readCategories(userTables, id):
    categories = []
    for table in userTables:
        print(table["main_table"])
        categories += db.execute("SELECT category, main_table FROM userTables WHERE user_id = ? AND main_table = ?", id, table["main_table"])
    print(categories)
    return categories


@app.route("/")
def index():

    # Function to return userTables and categories
    user_id = 522
    # Read tables belonging to id 522
    userTables = readTables(user_id)

    # Read categories from passed tables belonging to id 522
    categories = readCategories(userTables, user_id)
    
    print("User visited index page")
    return render_template("index.html", userTables=userTables, categories=categories)


@app.route("/manage", methods=["GET", "POST"])
def manage():

    # Function to return userTables and categories
    user_id = 522
    # Read tables belonging to id 522
    userTables = readTables(user_id)

    # Read categories from passed tables belonging to id 522
    categories = readCategories(userTables, user_id)

    print("User visited manage page")
    return render_template("manage.html", userTables=userTables, categories=categories)


@app.route("/add", methods=["GET", "POST"])
def add():
    print("User visited add page")
    if request.method == "POST":
        table = request.form.get("table")
        category = request.form.get("category")

        # Create a function that does everything below so it will take less space
        addTableToSQL(table, category)

    return redirect("add.html")


@app.route("/delete", methods=["GET", "POST"])
def delete():
    print("User visited delete page")
    if request.method == "POST":
        table = request.form.get("table")
        category = request.form.get("category")

        # Create a function that does everything below so it will take less space
        # deleteTableFromSQL(table, category)
                
        return redirect("manage.html")


# Tests for urls at the start of flask server
with app.test_request_context():
    print(url_for("index"))
    print(url_for("add"))