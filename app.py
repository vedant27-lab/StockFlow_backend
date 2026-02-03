from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
from jose import jwt
import requests
from functools import wraps

load_dotenv()

app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DB")
)


def cursor():
    return db.cursor(dictionary=True)

ATLAS_APP_ID = os.getenv("")
JWKS_URL = f""

jwks = request.get(JWKS_URL).json()


@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    cur = cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        return jsonify({"error": "Email already exists"}), 400
    
    password_hash = generate_password_hash(password)

    cur.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s,%s,%s)",
        (name, email, password_hash)
    )
    db.commit()

    return jsonify({"message": "User created Successfully"}), 200

@app.route("/login", methods=["POST"])
def login():
    data = request.data
    email = data.get("email")
    password = data.get("password")

    cur = cursor()
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    token = create_access_token(
        identity={"id": user["id"], "role": user["role"]}
    )

    return jsonify({
        "access_token": token,
        "role": user["role"]
    })
def admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = get_jwt_identity()
        if user["role"] != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    wrapper.__name__= fn.__name__
    return wrapper

@app.route("/fields", methods=["POST"])
@admin_required
def create_field():
    data = request.json
    cur = cursor()
    cur.execute(
        """INSERT INTO product_fields
        (field_name, field_type, is_required)
        VALUES (%s,%s,%s)""",
        (data["name"], data["type"], data.get("required", False))
    )
    db.commit()
    return jsonify({"message": "Field created"})

@app.route("/me", methods=["GET"])
@jwt_required()
def me():
    return jsonify(get_jwt_identity())
