from cs50 import SQL
from flask import Flask, url_for, render_template, request, session, redirect
from flask_session import Session
from datetime import timedelta

# Flask will use directory of app.py to search for templates and static
app = Flask(__name__)

# Set the secret key so users will not be able to change session cookie information
app.secret_key = "af3c081ff9e7c80f132f848ea44f0a1fd89cf5388a517edbe268dcb3d9f57c9a"

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=28)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///app.db")

# Check if there are any tables with that name and user_id
def tableExists(table):
    if len(db.execute("SELECT main_table FROM userTables WHERE user_id = ? AND main_table = ?", session["id"], table)) == 0:
        return 0
    else:
        return 1


def categoryExists(table, category):
    if len(db.execute("SELECT main_table FROM userTables WHERE user_id = ? AND main_table = ? AND category = ?", session["id"], table, category)) == 0:
        return 0
    else:
        return 1


def wordExists(category, word):
    if len(db.execute("SELECT main_table FROM userTables WHERE user_id = ? AND category = ? AND words = ?", session["id"], category, word)) == 0:
        return 0
    else:
        return 1


def aTableToSQL(table):
    if tableExists(table) == 0:
        print("Dictionary is empty. Creating new table")
        db.execute("INSERT INTO userTables (user_id, main_table) VALUES (?, ?)", session["id"], table)
    else:
        print("Dictionary exists")


def aCategoryToTable(table, category):
    # Delete Null category
    db.execute("DELETE FROM userTables WHERE main_table = ? AND user_id = ? AND category IS NULL", table, session["id"])

    if categoryExists(table, category, id) == 0:
        print(f"Adding category {category} to table")
        db.execute("INSERT INTO userTables (user_id, main_table, category) VALUES (?, ?, ?)", session["id"], table, category)
    else:
        print("Such category already exists")


def aWordToCategory(table, category, word):
    # Delete Null words
    db.execute("DELETE FROM userTables WHERE main_table = ? AND user_id = ? AND category = ? AND words IS NULL", table, session["id"], category)
    if wordExists(category, word) == 0:
        print(f"Adding word {word} to table")
        db.execute("INSERT INTO userTables (user_id, main_table, category, words) VALUES (?, ?, ?, ?)", session["id"], table, category, word)
    else:
        print("Such word already exists")


def dTableFromSQL(table):
    db.execute("DELETE FROM userTables WHERE main_table = ? AND user_id = ?", table, session["id"])
    return


def dCategoryFromTable(table, category):
    db.execute("DELETE FROM userTables WHERE main_table = ? AND category = ? AND user_id = ?", table, category, session["id"])
    return

def dWordFromCategory(table, category, word):
    db.execute("DELETE FROM userTables WHERE main_table = ? AND category = ? AND words = ? AND user_id = ?", table, category, word, session["id"])
    return


# Function to read all tables belonging to user's id
def readTables():
    userTables = db.execute("SELECT DISTINCT main_table FROM userTables WHERE user_id = ? ORDER BY main_table ASC", session["id"])
    # print(userTables[0]["main_table"])
    return userTables
    


# Function to read categories from passed tables belonging to user's id
def readCategories(userTables):
    categories = []
    for table in userTables:
        print(table["main_table"])
        categories += db.execute("SELECT DISTINCT category, main_table FROM userTables WHERE user_id = ? AND main_table = ? ORDER BY category ASC", session["id"], table["main_table"])
    print(categories)
    return categories

def readWords(table, category):
    words = []
    words = db.execute("SELECT DISTINCT words FROM userTables WHERE user_id = ? AND main_table = ? AND category = ? ORDER BY main_table ASC", session["id"], table, category)
    print(words)
    return words


@app.route("/", methods=["GET", "POST"])
def index():
    # Handling cookies
    session["id"] = 522
    session["login"] = "Hikyn"

    # Look inside of a cookie
    print(session)
    print(session["testing"])

    # Read tables belonging to session ID
    userTables = readTables()
    if len(userTables) == 0:
        return render_template("index.html")

    # Read categories from passed tables belonging to session ID
    categories = readCategories(userTables)
    
    if request.method == "GET":
        # If session remembers your last visited tables and categories, it will display them
        try:
            if session["currentTable"] != "" and session["currentCategory"] != "":
                words = readWords(session["currentTable"], session["currentCategory"])
                return render_template("index.html", userTables=userTables, currentTable=session["currentTable"], categories=categories, currentCategory=session["currentCategory"], words=words)
        except KeyError:
            print("There are no last tables/categories/words in cookie")

        print("Default page with no selected tables")
        return render_template("index.html", userTables=userTables, categories=categories)

    if request.method == "POST":
        strToSplit = request.form.get("request")
        strToSplit = strToSplit.split("-")
        table = strToSplit[0]
        category = strToSplit[1]
        currentTable = table
        currentCategory = category
        print(currentTable)
        print(currentCategory)
        words = readWords(table, category)
        if len(words) == 0:
            return render_template("index.html", userTables=userTables, categories=categories)
        # If category is not empty, it will render everything and store last table/category/words in cookie
        session["currentTable"] = currentTable
        session["currentCategory"] = currentCategory
        return render_template("index.html", userTables=userTables, currentTable=currentTable, categories=categories, currentCategory=currentCategory, words=words)


@app.route("/manage", methods=["GET", "POST"])
def manage():
    # Function to return userTables and categories
    userTables = readTables()
    if len(userTables) == 0:
        return render_template("manage.html")

    # Read categories from passed tables belonging to session["id"]
    categories = readCategories(userTables)
    if len(categories) == 0:
        return render_template("manage.html", userTables=userTables)

    print("User visited manage page")
    return render_template("manage.html", userTables=userTables, categories=categories)



@app.route("/addTable", methods=["POST"])
def addTable():
    if request.method == "POST":
        table = request.form.get("table")
        print(f"Trying to add table {table}")
        aTableToSQL(table)

    return redirect("/manage")

@app.route("/addCategory", methods=["POST"])
def addCategory():
    if request.method == "POST":
        table = request.form.get("table")
        category = request.form.get("category")
        print(f"Trying to add category {category}")
        aCategoryToTable(table, category)

    return redirect("/manage")

@app.route("/addWord", methods=["POST"])
def addWord():
    print("User visited add Word page")
    if request.method == "POST":
        strToSplit = request.form.get("request")
        word = request.form.get("word")
        print(strToSplit.split("-"))
        strToSplit = strToSplit.split("-")
        table = strToSplit[0]
        category = strToSplit[1]
        print(f"Trying to add to table {table} category {category} WORD {word}")
        aWordToCategory(table, category, word)

        return redirect("/manage")

@app.route("/addWordOverview", methods=["POST"])
def addWordOverview():
    print("User visited add Word page")
    if request.method == "POST":
        word = request.form.get("wordAdd")
        table = request.form.get("table")
        category = request.form.get("category")
        print(f"Trying to add to table {table} category {category} WORD {word}")
        aWordToCategory(table, category, word)

        return redirect("/")


@app.route("/deleteTable", methods=["POST"])
def deleteTable():
    print("User visited delete Table page")
    if request.method == "POST":
        table = request.form.get("table")
        print(f"Trying to delete table {table}")
        dTableFromSQL(table)

        return redirect("/manage")

@app.route("/deleteCategory", methods=["POST"])
def deleteCategory():
    print("User visited delete Category page")
    if request.method == "POST":
        strToSplit = request.form.get("request")
        print(strToSplit.split("-"))
        strToSplit = strToSplit.split("-")
        table = strToSplit[0]
        category = strToSplit[1]
        print(f"Trying to delete from table {table} category {category}")
        dCategoryFromTable(table, category)

        return redirect("/manage")

@app.route("/deleteWord", methods=["POST"])
def deleteWord():
    print("User visited delete Word page")
    if request.method == "POST":
        strToSplit = request.form.get("request")
        word = request.form.get("word")
        print(strToSplit.split("-"))
        strToSplit = strToSplit.split("-")
        table = strToSplit[0]
        category = strToSplit[1]
        print(f"Trying to delete from table {table} category {category} WORD {word}")
        dWordFromCategory(table, category, word)

        return redirect("/manage")

@app.route("/deleteWordOverview", methods=["POST"])
def deleteWordOverview():
    if request.method == "POST":
        word = request.form.get("wordDel")
        table = request.form.get("table")
        category = request.form.get("category")
        print(f"Trying to delete from table {table} category {category} WORD {word}")
        dWordFromCategory(table, category, word)

        return redirect("/")

# Tests for urls at the start of flask server
# with app.test_request_context():
#    print(url_for("index"))
#    print(url_for("add"))