from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

CURRENT_USER_ID = 1

def get_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB")
    )
@app.route("/analytics/metrics", methods=["GET"])
def get_metrics():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT name FROM fields WHERE value='number'")
    metrics = [row['name'] for row in cur.fetchall()]
    cur.close()
    db.close()
    return jsonify(metrics)
@app.route("/analytics/data", methods=["GET"])
def get_analytics_data():
    metric_name = request.args.get('metric') 
    if not metric_name:
        return jsonify([])
    db = get_db()
    cur = db.cursor(dictionary=True)
    query = """
        SELECT 
            f.name as label, 
            COALESCE(SUM(CAST(v.value AS DECIMAL(10,2))), 0) as value
        FROM folders f
        JOIN fields fl ON f.id = fl.folder_id
        JOIN products p ON f.id = p.folder_id
        LEFT JOIN field_value v ON p.id = v.product_id AND v.field_id = fl.id
        WHERE fl.name = %s AND fl.field_type = 'number'
        GROUP BY f.id
    """
    cur.execute(query, (metric_name,))
    data = cur.fetchall()
    total = sum(d['value'] for d in data)
    cur.close()
    db.close()
    return jsonify({"chart_data": data, "total": total})
@app.route("/folders", methods=["GET", "POST"])
def manage_folders():
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "POST":
        data = request.json
        cur.execute("INSERT INTO folders (name) VALUES (%s)", (data['name'],))
        db.commit()
        new_id = cur.lastrowid
        cur.close()
        db.close()
        return jsonify({"id": new_id, "message": "Folder created"}), 201
    cur.execute("SELECT * FROM folders")
    folders = cur.fetchall()
    cur.close()
    db.close()
    return jsonify(folders)
@app.route("/fields", methods=["GET", "POST"])
def manage_fields():
    db = get_db()
    cur = db.cursor(dictionary=True)
    folder_id = request.args.get('folder_id')
    if request.method == "POST":
        data = request.json
        cur.execute(
            "INSERT INTO fields (name, field_type, folder_id) VALUES (%s, %s, %s)",
            (data['name'], data['type'], data['folder_id'])
        )
        db.commit()
        cur.close()
        db.close()
        return jsonify({"message": "Field created"}), 201
    cur.execute("SELECT * FROM fields WHERE folder_id = %s", (folder_id,))
    fields = cur.fetchall()
    cur.close()
    db.close()
    return jsonify(fields)
@app.route("/products", methods=["POST"])
def create_product():
    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO products (name, folder_id) VALUES (%s, %s)", (data['name'], data['folder_id']))
    pid = cur.lastrowid
    for field_id, val in data.get('values', {}).items():
        cur.execute("INSERT INTO field_value (product_id, field_id, value) VALUES (%s, %s, %s)", (pid, field_id, val))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"message": "Saved"}), 201
@app.route("/products", methods=["GET"])
def get_products():
    folder_id = request.args.get('folder_id')
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM products WHERE folder_id = %s", (folder_id,))
    products = cur.fetchall()
    for p in products:
        cur.execute("""
            SELECT f.id as field_id, f.name, f.field_type, v.value 
            FROM fields f 
            LEFT JOIN field_value v ON f.id = v.field_id AND v.product_id = %s
            WHERE f.folder_id = %s
        """, (p['id'], folder_id))
        p['values'] = cur.fetchall()
    cur.close()
    db.close()
    return jsonify(products)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    print("Server is running.")