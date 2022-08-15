from cs50 import SQL
from flask import Flask, flash, url_for, render_template, request, session, redirect
from flask_session import Session
from datetime import date, timedelta
import random
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

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


def tableToSQL(table):
    if tableExists(table) == 0:
        if len(table) <= 2:
            flash(f"Table name {table} is shorter than 3 symbols", "error")
            return
        # print("Dictionary is empty. Creating new table")
        db.execute("INSERT INTO userTables (user_id, main_table) VALUES (?, ?)", session["id"], table)
        flash(f"Table {table} was created", "success")
    else:
        flash(f"Table {table} already exists", "error")
        # print("Dictionary exists")


def categoryToTable(table, category):
    # Delete Null category
    db.execute("DELETE FROM userTables WHERE main_table = ? AND user_id = ? AND category IS NULL", table, session["id"])

    if categoryExists(table, category) == 0:
        # print(f"Adding category {category} to table")
        db.execute("INSERT INTO userTables (user_id, main_table, category) VALUES (?, ?, ?)", session["id"], table, category)
        flash(f"Category was added to {table}", "success")
    else:
        flash(f"Category {category} already exists in {table}", "error")
        # print("Such category already exists")


def wordToCategory(table, category, word, meaning):
    # Delete Null words
    db.execute("DELETE FROM userTables WHERE main_table = ? AND user_id = ? AND category = ? AND words IS NULL", table, session["id"], category)
    if wordExists(category, word) == 0:
        # print(f"Adding word {word} to table with meaning {meaning}")
        db.execute("INSERT INTO userTables (user_id, main_table, category, words, meaning) VALUES (?, ?, ?, ?, ?)", session["id"], table, category, word, meaning)
        flash(f"Word was added to {category}", "success")
    else:
        flash(f"Word {word} already exists in {category}", "error")
        # print("Such word already exists")


def tableFromSQL(table):
    if tableExists(table) == 1:
        db.execute("DELETE FROM userTables WHERE main_table = ? AND user_id = ?", table, session["id"])
        flash(f"Table {table} was deleted", "warning")
    else:
        flash(f"Table {table} does not exist", "error")
    return


def categoryFromTable(table, category):
    if categoryExists(table, category) == 1:
        db.execute("DELETE FROM userTables WHERE main_table = ? AND category = ? AND user_id = ?", table, category, session["id"])
        flash(f"Category {category} was deleted from {table}", "warning")
    else:
        flash(f"Category {category} does not exist in {table}", "error")
    return

def wordFromCategory(table, category, word, *argv):
    if wordExists(category, word) == 1:
        db.execute("DELETE FROM userTables WHERE main_table = ? AND category = ? AND words = ? AND user_id = ?", table, category, word, session["id"])
        flash(f"Word {word} was deleted from {category}", "warning")
    else:
        flash(f"Word {word} does not exist in {category}", "error")
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
        # print(table["main_table"])
        categories += db.execute("SELECT DISTINCT category, main_table FROM userTables WHERE user_id = ? AND main_table = ? ORDER BY category ASC", session["id"], table["main_table"])
    # print(categories)
    return categories


def readWords(table, category):
    words = []
    words = db.execute("SELECT DISTINCT words, meaning FROM userTables WHERE user_id = ? AND main_table = ? AND category = ? ORDER BY words ASC", session["id"], table, category)
    # print(words)
    return words

def writeQuizResults(quiz, table, category):
    for result in quiz:
        # Если уже есть запись за сегодня - тогда ее переписываем
        if len(db.execute("SELECT word FROM quiz WHERE user_id = ? AND main_table = ? AND category = ? AND word = ? AND date = ?", session["id"], table, category, result["words"], date.today())) == 0:
            print("There are no results of this quiz today. Inserting results")
            db.execute("INSERT INTO quiz (user_id, main_table, category, word, meaning, correctness, date) VALUES (?, ?, ?, ?, ?, ?, ?)", session["id"], table, category, result["words"], result["meaning"], result["correctness"], date.today())
        else:
            print("There are existing quiz results. Updating existing table")
            db.execute("UPDATE quiz SET correctness = ? WHERE user_id = ? AND main_table = ? AND category = ? AND word = ? AND date = ?", result["correctness"], session["id"], table, category, result["words"], date.today())


def quizRead(date, table, category):
    quiz = db.execute("SELECT * FROM quiz WHERE user_id = ? AND main_table = ? AND category = ? AND date = ?", session["id"], table, category, date.today())
    print(f"Result of reading quiz for today for category {category} and table {table}")
    return quiz

def newOrWrongWords(table, category, words):
    quizResults = quizRead(date.today(), table, category)
    toLearn = []
    # print("Words are: ", words)
    for word in words:
        # wordLearned ensures that we add word only once
        wordLearned = 0
        for quiz in quizResults:
            if word["words"] == quiz["word"]:
                wordLearned = 1
                if quiz["correctness"] == 0:
                    toLearn.append(quiz)
                    #If word was correct on quiz, add it to new dictionary
                # print(f"Word {word['words']} is found in quiz!")
        if wordLearned == 0:
            toLearn.append(word)
    return toLearn

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Handling cookies
    # session["id"] = 522
    # session["login"] = "Hikyn"

    session["currentWordInt"] = 0
    session["quiz"] = []
    session["quizVisited"] = 0
    session["lastWord"] = []

    # Setting default values
    correctAnswers = 0

    # Look inside of a cookie
    print(session)

    # Read tables belonging to session ID
    userTables = readTables()
    if len(userTables) == 0:
        return render_template("index.html")

    # Read categories from passed tables belonging to session ID
    categories = readCategories(userTables)

    

    if request.method == "GET":
        # Display results of a quiz for today if there is any
        quizResults = quizRead(date.today(), session.get("currentTable"), session.get("currentCategory"))
        for quiz in quizResults:
            # print("Successfully found quiz results")
            if quiz["correctness"] == 1:
                correctAnswers += 1
        session["correctAnswers"] = correctAnswers
        # print(f"Right now there are {session['correctAnswers']} correct results")
        # print(f"Quiz results are: {quizResults}")
        # If session remembers your last visited tables and categories, it will display them
        try:
            if session.get("editTables") == 1:
                print("EDIT table pressed")
                return render_template("index.html", userTables=userTables, categories=categories)
            
            if session.get("editCategories") == 1:
                print("Edit categories is pressed")
                return render_template("index.html", userTables=userTables, categories=categories)
            
            if session["currentTable"] != "" and session["currentCategory"] != "":
                print("Table and Category are selected")
                words = readWords(session["currentTable"], session["currentCategory"])
                print("Rendering template with currentTable and currentCategory")
                return render_template("index.html", userTables=userTables, categories=categories, words=words, quizResults=quizResults)      

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
        # print(currentTable)
        # print(currentCategory)
        words = readWords(table, category)
        if len(words) == 0:
            return render_template("index.html", userTables=userTables, categories=categories)

        # If category is not empty, it will render everything and store last table/category/words in cookie
        session["currentTable"] = currentTable
        session["currentCategory"] = currentCategory

        # Display results of a quiz in a new category/table if there is any
        quizResults = quizRead(date.today(), session.get("currentTable"), session.get("currentCategory"))
        for quiz in quizResults:
            # print("Successfully found quiz results")
            if quiz["correctness"] == 1:
                correctAnswers += 1
        session["correctAnswers"] = correctAnswers
        print(f"Right now there are {session['correctAnswers']} correct results")
        print(f"Quiz results are: {quizResults}")
        return render_template("index.html", userTables=userTables, currentTable=currentTable, categories=categories, currentCategory=currentCategory, words=words, quizResults=quizResults)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username", "error")
            return redirect("/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password", "error")
            return redirect("/login")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password", "error")
            return redirect("/login")

        # Remember which user has logged in
        session["id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/", )

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        usernames = db.execute("SELECT username FROM users")
        registeredNames = []
        for i in usernames:
            registeredNames.append(i["username"])
        print(registeredNames)
        if " " in username or username == "":
            flash("Username is blank", "error")
            return redirect("/register")

        elif username in registeredNames:
            flash("Username already exists", "error")
            return redirect("/register")

        elif password != confirmation:
            flash("Passwords do not match", "error")
            return redirect("/register")

        elif " " in password or password == "":
            flash("Invalid password", "error")
            return redirect("/register")

        passwordHashed = generate_password_hash(password)
        print(passwordHashed)
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, passwordHashed)
        session["jRegistered"] = True
        return render_template("login.html")

    """Register user"""
    return apology("TODO")


@app.route("/learn", methods=["POST", "GET"])
@login_required
def learn():
    # If it is our first visi
    table = session.get("currentTable")
    category = session.get("currentCategory")
    words = readWords(table, category)
    toLearn = newOrWrongWords(table, category, words)
    session["translateLearn"] = 0
    if request.form.get("submit") == "wordsTranslation":
        print("User clicked Meaning")
        session["translateLearn"] = 1

    # Если мы не в режиме перевода
    if session["translateLearn"] == 0:
        randomNumber = random.randint(0, len(toLearn) - 1)
        session["randomNumber"] = randomNumber    
        # Чистим ключ у словаря
        for word in toLearn:
            if word.get("word") == None:
                word["word"] = word.pop("words")
        print(toLearn)
        # If word is the same as last word, we reroll it.
        word = toLearn[session["randomNumber"]]
        print(word)
        print(session["lastWord"])

        # Even more stupid fixes to words and word inconsistency
        if session["lastWord"].get("word") == None:
                session["lastWord"]["word"] = session["lastWord"].pop("words")

        while word["word"] == session["lastWord"]["word"]:
            print(f"Word {word['word']} is the same as lastWord {session['lastWord']['word']}, rerolling")
            session["randomNumber"] = random.randint(0, len(toLearn) - 1)
            word = toLearn[session["randomNumber"]]

    else:
        word = session["lastWord"]
        
    print("Последнее слово в кукисах: ", session["lastWord"]["word"])
    print("Слово для показа: ", word["word"])
    
    session["lastWord"] = word
    #print("To learn: ", toLearn)
    if session.get("translateLearn") != 1:
        session["translateLearn"] = 0  
    return render_template("learn.html", table=table, category=category, word=word)


@app.route("/quiz", methods=["POST", "GET"])
@login_required
def quiz():
    # If it is our first visit
    if session["quizVisited"] == 0:
        table = session.get("currentTable")
        category = session.get("currentCategory")
        words = readWords(table, category)
        session["randInts"] = random.sample(range(0, len(words)), len(words))
        session["quizVisited"] = 1
        session["currentWordInt"] = 0
        session["translateQuiz"] = 0  
        

    session["translateQuiz"] = 0  
    
    # Get all necessary values
    table = session.get("currentTable")
    category = session.get("currentCategory")
    words = readWords(table, category)

    # We receive random seed from cookie
    randInts = session["randInts"]

    # Check if they are staying the same
    # print(randInts)
    if request.form.get("submit") == "wordsTranslation":
        print("User clicked Meaning")
        session["translateQuiz"] = 1

    if session["translateQuiz"] == 0:
        # Check if currentWordInt exceeding the list of words
        if session.get("currentWordInt") > (len(words) - 1):
            currentWordInt = session.get("currentWordInt")
            word = words[randInts[currentWordInt - 1]]
            if request.form.get("submit") == "correct":
                word["correctness"] = 1
            else:
                word["correctness"] = 0
            session["quiz"].append(word)
            flash("You have finished the quiz!", "success")
            print("Current position reached the end")
            print(f"Quiz cookie: {session['quiz']}")
            writeQuizResults(session["quiz"], table, category)
            # Clear current quiz
            session["quiz"] = ""
            return redirect("/")
        
        currentWordInt = session.get("currentWordInt")
        print(f"Current question number {currentWordInt}")
        word = words[randInts[currentWordInt]]
        print(f"Picked word: {word}")

        # Если на прошлое слово ответили "правильно"
        if currentWordInt >= 1 and request.form.get("submit") == "correct":
            print("Correct button was pressed")
            session["currentWordInt"] += 1
            prevWord = words[randInts[currentWordInt - 1]]
            prevWord["correctness"] = 1
            session["quiz"].append(prevWord)

        # Если на прошлое слово ответили "неправильно"
        elif currentWordInt >= 1 and request.form.get("submit") == "wrong":
            print("Wrong button was pressed")
            session["currentWordInt"] += 1
            prevWord = words[randInts[currentWordInt - 1]]
            prevWord["correctness"] = 0
            session["quiz"].append(prevWord)

        elif request.form.get("submit") == "wordsTranslation":
            print("User clicked Meaning")
            session["translateQuiz"] = 1

        else:
            session["currentWordInt"] += 1

        if len(words) == 0:
            flash("There was no active table and category", "error")
            return redirect("/")
        session["lastWord"] = word
    else:
        word = session["lastWord"]

    print(f"Length of words: {len(words)}")
    progress = int((session["currentWordInt"] / len(words)) * 100)
    print(f"Completion percent: {progress}")
    return render_template("quiz.html", table=table, category=category, word=word, length=len(words), progress=progress)


@app.route("/manage", methods=["GET", "POST"])
@login_required
def manage():
    # Function to return userTables and categories
    userTables = readTables()

    # Stopping editing of overview
    session["editCategories"] = 0
    if len(userTables) == 0:
        return render_template("manage.html")

    # Read categories from passed tables belonging to session["id"]
    categories = readCategories(userTables)
    if len(categories) == 0:
        return render_template("manage.html", userTables=userTables)

    print("User visited manage page")
    return render_template("manage.html", userTables=userTables, categories=categories)


@app.route("/addTable", methods=["POST"])
@login_required
def addTable():
    if request.method == "POST":
        table = request.form.get("table")
        print(f"Trying to add table {table}")
        tableToSQL(table)

    return redirect("/manage")


@app.route("/addCategory", methods=["POST"])
@login_required
def addCategory():
    if request.method == "POST":
        table = request.form.get("table")
        category = request.form.get("category")
        print(f"Trying to add category {category}")
        categoryToTable(table, category)
        # Return user back to manage
        return redirect("/manage")


@app.route("/addWord", methods=["POST"])
@login_required
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
        wordToCategory(table, category, word)

        return redirect("/manage")


@app.route("/changeTablesOverview", methods=["POST"])
@login_required
def changeTableOverview():
    if request.method == "POST":
        submit = request.form.get("submit")
        table = request.form.get("table")
        if submit == "add":
            print(f"Trying to add to table {table}")
            tableToSQL(table)
            return redirect("/")

        elif submit == "delete":
            print(f"Trying to delete from table {table}")
            tableFromSQL(table)
            return redirect("/")

        return redirect("/")


@app.route("/changeCategoryOverview", methods=["POST"])
@login_required
def changeCategoryOverview():
    if request.method == "POST":
        submit = request.form.get("submit")
        table = request.form.get("table")
        category = request.form.get("category")
        word = request.form.get("word")
        if submit == "add":
            print(f"Trying to add category {category} to table {table}")
            categoryToTable(table, category)
            return redirect("/")

        elif submit == "delete":
            print(f"Trying to delete category {category} from table {table}")
            categoryFromTable(table, category)
            return redirect("/")

        elif submit == "editCategory":
            session["currentTable"] = table
            session["currentCategory"] = ""
            print("Trying to edit categories in overview")
            session["wordsTranslation"] = 0
            session["editTables"] = 0
            session["editCategories"] = 1
        
        elif submit == "stopEditCategory":
            session["currentTable"] = table
            session["currentCategory"] = ""
            print("Trying to stop editing categories in overview")
            session["wordsTranslation"] = 0
            session["editTables"] = 0
            session["editCategories"] = 0

        elif submit == "editTables":
            session["currentTable"] = ""
            print("Trying to edit tables")
            session["currentCategory"] = ""
            session["wordsTranslation"] = 0
            session["editCategories"] = 0
            session["editTables"] = 1

        elif submit == "stopEditTables":
            session["currentTable"] = ""
            print("Trying to stop editing tables")
            session["currentCategory"] = ""
            session["wordsTranslation"] = 0
            session["editCategories"] = 0
            session["editTables"] = 0

        return redirect("/")


@app.route("/changeWordOverview", methods=["POST"])
@login_required
def changeWordOverview():
    if request.method == "POST":
        submit = request.form.get("submit")
        table = request.form.get("table")
        category = request.form.get("category")
        word = request.form.get("word")
        meaning = request.form.get("meaning")
        session["editTables"] = 0
        session["editCategories"] = 0
        if submit == "add":
            if len(word) == 0:
                print("Empty word")
                flash("Entered word is empty", "error")
                return redirect("/")
            elif len(meaning) == 0:
                print("Empty meaning")
                flash(f"Meaning field of word {word} is empty", "error")
                return redirect("/")
            print(f"Trying to add to table {table} category {category} WORD {word} MEANING {meaning}")
            wordToCategory(table, category, word, meaning)

        elif submit == "delete":
            print(f"Trying to delete from table {table} category {category} WORD {word}")
            wordFromCategory(table, category, word, meaning)

        elif submit == "wordsTranslation":
            print("Trying to translate words")
            session["wordsTranslation"] = 1

        elif submit == "wordsTranslationStop":
            print("Trying to stop translating words")
            session["wordsTranslation"] = 0

        elif submit == "editWords":
            print("Trying to edit words")
            session["editWords"] = 1

        elif submit == "stopEditWords":
            print("Trying to stop editing words")
            session["editWords"] = 0

        return redirect("/")


@app.route("/deleteTable", methods=["POST"])
@login_required
def deleteTable():
    print("User visited delete Table page")
    if request.method == "POST":
        table = request.form.get("table")
        print(f"Trying to delete table {table}")
        tableFromSQL(table)

        return redirect("/manage")

@app.route("/deleteCategory", methods=["POST"])
@login_required
def deleteCategory():
    print("User visited delete Category page")
    if request.method == "POST":
        strToSplit = request.form.get("request")
        print(strToSplit.split("-"))
        strToSplit = strToSplit.split("-")
        table = strToSplit[0]
        category = strToSplit[1]
        print(f"Trying to delete from table {table} category {category}")
        categoryFromTable(table, category)
        # Return user back to manage
        return redirect("/manage")


@app.route("/deleteWord", methods=["POST"])
@login_required
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
        wordFromCategory(table, category, word)

        return redirect("/manage")


# Tests for urls at the start of flask server
# with app.test_request_context():
#    print(url_for("index"))
#    print(url_for("add"))