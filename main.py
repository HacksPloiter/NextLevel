import hashlib
import random
import string
import bcrypt
from flask import Flask, request, make_response, render_template, redirect, url_for, send_from_directory
from pymongo import MongoClient
import helpers

app = Flask(__name__)
mongo_client = MongoClient("mongo")  # Ensure this is your correct connection string
db = mongo_client["next-level"]
userpass = db["userpass"]
usertoken = db["usertoken"]
teampts = db["teampts"]


@app.route('/')
def index():
    allcookies = request.cookies
    response = make_response(render_template('index.html'))
    visits = int(allcookies.get('visits', 0)) + 1
    response.set_cookie('visits', str(visits), max_age=3600)
    return response


@app.route('/game')
def game():
    user = ""
    token = request.cookies.get('token')
    if token:
        user_data = usertoken.find_one({"token": token})
        if user_data:
            user = user_data.get("username", "")
    return render_template('game.html', team=user)


@app.route('/leaderboard')
def leaderboard():
    # Improved leaderboard calculation logic
    leaderboarddic = {}
    for entry in teampts.find():
        username = entry.get("username")
        questions = entry.get("questions", [])
        for q in questions:
            points = 10  # Default points, modify as per your scoring system
            leaderboarddic[username] = leaderboarddic.get(username, 0) + points

    sortLead = helpers.sort_teams(leaderboarddic)
    leader = "<br>".join(f"{team} : {score}" for team, score in sortLead.items())

    response = make_response(render_template('leaderboard.html', leader=leader))
    visits = int(request.cookies.get('visits', 0)) + 1
    response.set_cookie('visits', str(visits), max_age=3600)
    return response


@app.route('/mentors')
def mentors():
    allcookies = request.cookies
    response = make_response(render_template('mentors.html'))
    visits = int(allcookies.get('visits', 0)) + 1
    response.set_cookie('visits', str(visits), max_age=3600)
    return response


@app.route('/login')
def login():
    allcookies = request.cookies
    response = make_response(render_template('login.html'))
    visits = int(allcookies.get('visits', 0)) + 1
    response.set_cookie('visits', str(visits), max_age=3600)
    return response


@app.route('/schedule')
def schedule():
    allcookies = request.cookies
    response = make_response(render_template('schedule.html'))
    visits = int(allcookies.get('visits', 0)) + 1
    response.set_cookie('visits', str(visits), max_age=3600)
    return response


@app.route('/registeruser', methods=['POST'])
def register_user():
    username = request.form.get('username')
    password = request.form.get('regpass')
    if not helpers.is_valid_input(username) or not helpers.is_valid_input(password):
        return "Invalid input", 400

    if userpass.find_one({"username": username}):
        return "Username already exists", 400

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    userpass.insert_one({"username": username, "password": password_hash})
    return redirect(url_for('login'))


@app.route('/loginuser', methods=['POST'])
def login_user():
    username = request.form.get('usernamel')
    password = request.form.get('regpassl')

    if not helpers.is_valid_input(username) or not helpers.is_valid_input(password):
        return "Invalid input", 400

    user = userpass.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode(), user["password"]):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=200))
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        usertoken.insert_one({"username": username, "token": token_hash})
        response = make_response(redirect(url_for('game')))
        response.set_cookie('token', token_hash, max_age=3600)
        return response
    else:
        return "Username not found or password is incorrect", 400


@app.route('/submit', methods=['POST'])
def submit():
    token = request.cookies.get('token')
    if not token:
        return "No token provided", 403

    user_data = usertoken.find_one({"token": token})
    if not user_data:
        return "User not authenticated", 403

    username = user_data["username"]
    correct_answers = {
        "Q1": "AMDFH", "Q2": "LNSGE", "Q3": "RMSGT", "Q4": "SZZJK", "Q5": "TMMAR",
        "Q6": "TVSGH", "Q7": "ALPXZ", "Q8": "XMRKM", "Q9": "WHLPS", "Q10": "JSDRJ",
        "Q11": "XWEWY", "Q12": "PYMJT", "Q13": "BWUFL", "Q14": "WPPQB", "Q15": "DHJPK"
    }
    questions_correct = []
    for q, answer in correct_answers.items():
        user_answer = request.form.get(q)
        if user_answer and user_answer == answer:
            questions_correct.append(q)

    if questions_correct:
        teampts.update_one({"username": username}, {"$push": {"questions": {"$each": questions_correct}}}, upsert=True)

    return redirect(url_for('leaderboard'))


@app.route('/assets/img/mentors/<filename>')
def mentor_image(filename):
    return send_from_directory('static/img/mentors', filename)


@app.route('/assets/img/others/<filename>')
def other_image(filename):
    return send_from_directory('static/img/others', filename)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)
