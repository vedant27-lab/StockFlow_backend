from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

def get_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB")
    )

# --- ANALYTICS ---
@app.route("/analytics/metrics", methods=["GET"])
def get_analytics_metrics():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT name FROM fields WHERE field_type = 'number'")
    metrics = [row['name'] for row in cur.fetchall()]
    cur.close()
    db.close()
    return jsonify(metrics)

@app.route("/analytics/data", methods=["GET"])
def get_analytics_data():
    metric_name = request.args.get('metric')
    if not metric_name:
        return jsonify({"labels": [], "values": [], "total": 0})

    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Sum up the value for every folder that has this metric
    query = """
        SELECT 
            f.name as label, 
            COALESCE(SUM(CAST(NULLIF(v.value, '') AS DECIMAL(10,2))), 0) as value
        FROM folders f
        JOIN fields fl ON f.id = fl.folder_id
        JOIN products p ON f.id = p.folder_id
        LEFT JOIN field_values v ON p.id = v.product_id AND v.field_id = fl.id
        WHERE fl.name = %s AND fl.field_type = 'number'
        GROUP BY f.id
    """
    cur.execute(query, (metric_name,))
    data = cur.fetchall()
    
    # Format for Charts (Lists are easier for Bar/Line charts)
    labels = []
    values = []
    total = 0.0

    for row in data:
        val = float(row['value'])
        labels.append(row['label'])
        values.append(val)
        total += val
    
    cur.close()
    db.close()
    return jsonify({
        "labels": labels, 
        "values": values, 
        "total": total
    })

# --- CRUD ROUTES ---
@app.route("/folders", methods=["GET", "POST"])
def manage_folders():
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "POST":
        data = request.json
        cur.execute("INSERT INTO folders (name) VALUES (%s)", (data['name'],))
        db.commit()
        return jsonify({"message": "Created"}), 201
    cur.execute("SELECT * FROM folders")
    res = cur.fetchall()
    cur.close()
    db.close()
    return jsonify(res)

@app.route("/folders/<int:id>", methods=["PUT"])
def update_folders(id):
    data = request.data
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE folders SET name=%s WHERE id=%s", (data['name'], id))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"message": "Folder updated"})

@app.route("/fields/<int:id>", methods=["PUT"])
def update_field(id):
    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE fields SET name=%s WHERE id=%s", (data['name'], id))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"message": "Field updated"})

@app.route("/fields/<int:id>", methods=["DELETE"])
def delete_field(id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM fields WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"message": "Field deleted"})

@app.route("/fields", methods=["GET", "POST"])
def manage_fields():
    db = get_db()
    cur = db.cursor(dictionary=True)
    folder_id = request.args.get('folder_id')
    if request.method == "POST":
        data = request.json
        cur.execute("INSERT INTO fields (name, field_type, folder_id) VALUES (%s, %s, %s)",
                    (data['name'], data['type'], data['folder_id']))
        db.commit()
        return jsonify({"message": "Created"}), 201
    cur.execute("SELECT * FROM fields WHERE folder_id = %s", (folder_id,))
    res = cur.fetchall()
    cur.close()
    db.close()
    return jsonify(res)

@app.route("/products", methods=["GET", "POST"])
def manage_products():
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    if request.method == "POST":
        data = request.json
        cur.execute("INSERT INTO products (name, folder_id) VALUES (%s, %s)", (data['name'], data['folder_id']))
        pid = cur.lastrowid
        for fid, val in data.get('values', {}).items():
            cur.execute("INSERT INTO field_values (product_id, field_id, value) VALUES (%s, %s, %s)", (pid, fid, val))
        db.commit()
        return jsonify({"message": "Saved"}), 201

    folder_id = request.args.get('folder_id')
    cur.execute("SELECT * FROM products WHERE folder_id = %s", (folder_id,))
    products = cur.fetchall()
    
    # Attach values
    for p in products:
        cur.execute("""
            SELECT f.id, f.name, v.value 
            FROM fields f 
            LEFT JOIN field_values v ON f.id = v.field_id AND v.product_id = %s
            WHERE f.folder_id = %s
        """, (p['id'], folder_id))
        p['values'] = cur.fetchall()

    cur.close()
    db.close()
    return jsonify(products)

@app.route("/products/<int:id>", methods=["DELETE"])
def delete_product(id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"message": "Deleted"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)