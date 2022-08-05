from cs50 import SQL
from flask import Flask, url_for, render_template, request, session

# Flask will use directory of app.py to search for templates and static
app = Flask(__name__)

# Set the secret key so users will not be able to change session cookie information
app.secret_key = "af3c081ff9e7c80f132f848ea44f0a1fd89cf5388a517edbe268dcb3d9f57c9a"

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///app.db")

@app.route("/")
def index():
    userTables = db.execute("SELECT DISTINCT main_table FROM userTables WHERE user_id = 522 ORDER BY main_table ASC")
    print(userTables[0]["main_table"])
    categories = []
    for table in userTables:
        print(table["main_table"])
        categories += db.execute("SELECT category, main_table FROM userTables WHERE user_id = 522 AND main_table = ?", table["main_table"])
    print(categories)
    print("User visited index page")
    return render_template("index.html", userTables=userTables, categories=categories)

@app.route("/add", methods=["GET", "POST"])
def add():
    print("User visited add page")
    if request.method == "POST":
        table = request.form.get("table")
        category = request.form.get("category")
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
                
        return render_template("add.html")
    return render_template("add.html")


# Tests for urls at the start of flask server
with app.test_request_context():
    print(url_for("index"))
    # print(url_for("add"))