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


# Check if there are any tables with that name and user_id
def tableExists(table, id):
    if len(db.execute("SELECT main_table FROM userTables WHERE user_id = 522 AND main_table = ?", table)) == 0:
        return 0
    else:
        return 1


def categoryExists(category, id):
    if len(db.execute("SELECT main_table FROM userTables WHERE user_id = 522 AND category = ?", category)) == 0:
        return 0
    else:
        return 1


def wordExists(word, id):
    if len(db.execute("SELECT main_table FROM userTables WHERE user_id = 522 AND words = ?", word)) == 0:
        return 0
    else:
        return 1


def aTableToSQL(table, id):
    if tableExists(table, id) == 0:
        print("Dictionary is empty. Creating new table")
        db.execute("INSERT INTO userTables (user_id, main_table) VALUES (?, ?)", id, table)
    else:
        print("Dictionary exists")


def aCategoryToTable(table, category, id):
    # Delete Null category
    db.execute("DELETE FROM userTables WHERE main_table = ? AND user_id = ? AND category IS NULL", table, id)

    if categoryExists(category, id) == 0:
        print(f"Adding category {category} to table")
        db.execute("INSERT INTO userTables (user_id, main_table, category) VALUES (?, ?, ?)", id, table, category)
    else:
        print("Such category already exists")


def aWordToCategory(table, category, word, id):
    # Delete Null words
    db.execute("DELETE FROM userTables WHERE main_table = ? AND user_id = ? AND category = ? AND words IS NULL", table, id, category)
    if wordExists(word, id) == 0:
        print(f"Adding word {word} to table")
        db.execute("INSERT INTO userTables (user_id, main_table, category, words) VALUES (?, ?, ?, ?)", id, table, category, word)
    else:
        print("Such word already exists")


def dTableFromSQL(table, id):
    db.execute("DELETE FROM userTables WHERE main_table = ? AND user_id = ?", table, id)
    return


def dCategoryFromTable(table, category, id):
    db.execute("DELETE FROM userTables WHERE main_table = ? AND category = ? AND user_id = ?", table, category, id)
    return


# Function to read all tables belonging to user's id
def readTables(id):
    userTables = db.execute("SELECT DISTINCT main_table FROM userTables WHERE user_id = ? ORDER BY main_table ASC", id)
    # print(userTables[0]["main_table"])
    return userTables


# Function to read categories from passed tables belonging to user's id
def readCategories(userTables, id):
    categories = []
    for table in userTables:
        print(table["main_table"])
        categories += db.execute("SELECT DISTINCT category, main_table FROM userTables WHERE user_id = ? AND main_table = ? ORDER BY category ASC", id, table["main_table"])
    print(categories)
    return categories

def readWords(table, category, id):
    words = []
    words = db.execute("SELECT DISTINCT words FROM userTables WHERE user_id = ? AND main_table = ? AND category = ? ORDER BY main_table ASC", id, table, category)
    print(words)
    return words


@app.route("/", methods=["GET", "POST"])
def index():
    # Function to return userTables and categories
    user_id = 522
    # Read tables belonging to id 522
    userTables = readTables(user_id)
    if len(userTables) == 0:
        return render_template("index.html")

    # Read categories from passed tables belonging to id 522
    categories = readCategories(userTables, user_id)
    
    if request.method == "GET":
        print("User visited index page")
        return render_template("index.html", userTables=userTables, categories=categories)

    if request.method == "POST":
        strToSplit = request.form.get("request")
        strToSplit = strToSplit.split("-")
        table = strToSplit[0]
        category = strToSplit[1]
        print(table)
        print(category)
        words = readWords(table, category, user_id)
        #print("User visited manage page VIA POST")
        return render_template("index.html", userTables=userTables, categories=categories, words=words)


@app.route("/manage", methods=["GET", "POST"])
def manage():
    # Function to return userTables and categories
    user_id = 522
    # Read tables belonging to id 522
    userTables = readTables(user_id)
    if len(userTables) == 0:
        return render_template("manage.html")

    # Read categories from passed tables belonging to id 522
    categories = readCategories(userTables, user_id)
    if len(categories) == 0:
        return render_template("manage.html", userTables=userTables)

    print("User visited manage page")
    return render_template("manage.html", userTables=userTables, categories=categories)



@app.route("/addTable", methods=["POST"])
def addTable():
    if request.method == "POST":
        id = 522
        table = request.form.get("table")
        print(f"Trying to add table {table}")
        aTableToSQL(table, id)

    return redirect("/manage")

@app.route("/addCategory", methods=["POST"])
def addCategory():
    if request.method == "POST":
        id = 522
        table = request.form.get("table")
        category = request.form.get("category")
        print(f"Trying to add category {category}")
        aCategoryToTable(table, category, id)

    return redirect("/manage")

@app.route("/addWord", methods=["POST"])
def addWord():
    print("User visited add Word page")
    if request.method == "POST":
        id = 522
        strToSplit = request.form.get("request")
        word = request.form.get("word")
        print(strToSplit.split("-"))
        strToSplit = strToSplit.split("-")
        table = strToSplit[0]
        category = strToSplit[1]
        print(f"Trying to add to table {table} category {category} WORD {word}")
        aWordToCategory(table, category, word, id)

        return redirect("/manage")


@app.route("/deleteTable", methods=["POST"])
def deleteTable():
    print("User visited delete Table page")
    if request.method == "POST":
        id = 522
        table = request.form.get("table")
        print(f"Trying to delete table {table}")
        dTableFromSQL(table, id)

        return redirect("/manage")

@app.route("/deleteCategory", methods=["POST"])
def deleteCategory():
    print("User visited delete Category page")
    if request.method == "POST":
        id = 522
        strToSplit = request.form.get("request")
        print(strToSplit.split("-"))
        strToSplit = strToSplit.split("-")
        table = strToSplit[0]
        category = strToSplit[1]
        print(f"Trying to delete from table {table} category {category}")
        dCategoryFromTable(table, category, id)

        return redirect("/manage")

# Tests for urls at the start of flask server
# with app.test_request_context():
#    print(url_for("index"))
#    print(url_for("add"))