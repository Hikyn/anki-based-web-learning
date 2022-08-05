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
    EnglishA1 = db.execute("SELECT * FROM EnglishA1 ORDER BY category ASC")
    print("User visited index page")
    return render_template("index.html", EnglishA1=EnglishA1)

# @app.route("/add")
# def add():
    if request.method == "POST":
        table = request.form.get("table")
        category = request.form.get("category")
    print("User visited add page")
    return render_template("add.html")


# Tests for urls at the start of flask server
with app.test_request_context():
    print(url_for("index"))
    # print(url_for("add"))