from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__, template_folder="templates")
app.secret_key = "secretkey123"


# ---------- MYSQL CONNECTION ----------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="onlinevoting"
    )


# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # ---------- ADMIN LOGIN ----------
        if username == "admin" and password == "admin":

            session["username"] = "admin"
            session["role"] = "admin"

            return redirect("/admin")

        # ---------- VOTER LOGIN ----------
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, password FROM voters WHERE username=%s",
            (username,)
        )

        user = cursor.fetchone()
        conn.close()

        if user and user[2] == password:

            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = "voter"

            return redirect("/vote")

        error = "Invalid username or password"

    return render_template("login.html", error=error)


# ---------- ADMIN DASHBOARD ----------
@app.route("/admin")
def admin_dashboard():

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()

    # Prepare data for chart
    labels = []
    votes = []

    for c in candidates:
        labels.append(c[1])
        votes.append(c[2])

    return render_template(
        "admin_dashboard.html",
        candidates=candidates,
        labels=labels,
        votes=votes
    )

# ---------- ADD VOTER ----------
@app.route("/add_voter", methods=["GET", "POST"])
def add_voter():

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    message = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO voters(username,password,voted) VALUES(%s,%s,0)",
            (username, password)
        )

        conn.commit()
        conn.close()

        message = "Voter added successfully"

    return render_template("add_voter.html", message=message)


# ---------- VIEW VOTERS ----------
@app.route("/view_voters")
def view_voters():

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM voters")
    voters = cursor.fetchall()

    return render_template(
        "view_voters.html",
        voters=voters
    )


# ---------- VOTING PAGE ----------
# ---------- VOTING PAGE ----------
@app.route("/vote", methods=["GET","POST"])
def vote():

    # only voter can access
    if "role" not in session or session["role"] != "voter":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()

    # check if voter already voted
    cursor.execute(
        "SELECT voted FROM voters WHERE id=%s",
        (session["user_id"],)
    )

    voted = cursor.fetchone()

    # if already voted show message
    if voted[0] == 1:
        return render_template(
            "vote.html",
            already_voted=True
        )

    # submit vote
    if request.method == "POST":

        candidate_id = request.form["candidate"]

        # increase vote count
        cursor.execute(
            "UPDATE candidates SET votes = votes + 1 WHERE id=%s",
            (candidate_id,)
        )

        # mark voter as voted
        cursor.execute(
            "UPDATE voters SET voted=1 WHERE id=%s",
            (session["user_id"],)
        )

        db.commit()

        return render_template("vote_success.html")

    # fetch candidates
    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()

    return render_template(
        "vote.html",
        candidates=candidates,
        already_voted=False
    )


# ---------- RESULT (ADMIN ONLY) ----------
@app.route("/result")
def result():

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM candidates")
    results = cursor.fetchall()

    return render_template(
        "result.html",
        results=results
    )


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- RUN SERVER ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)