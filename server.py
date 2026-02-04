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

@app.route("/dashboard", methods=["GET"])
def get_dashboard_stats():
    db = get_db()
    cur = db.cursor(dictionary=True)

    query = """
        SELECT 
            f.id as folder_id,
            f.name as folder_name,
            COUNT(DISTINCT p.id) as product_count,
            COALESCE(SUM(CAST(v.value AS UNSIGNED)), 0) as total_metric
        FROM product_folders f
        LEFT JOIN products p ON f.id = p.folder_id
        -- Join fields to find the one marked for analytics
        LEFT JOIN product_fields pf ON f.id = pf.folder_id AND pf.is_analytics_target = 1
        -- Join values ONLY for that specific analytics field
        LEFT JOIN product_field_values v ON p.id = v.product_id AND v.field_id = pf.id
        GROUP BY f.id
    """

    cur.execute(query)
    stats = cur.fetchall()

    grand_total = sum(item['total_metric'] for item in stats)

    cur.close()
    db.close()

    return jsonify({
        "stats": stats,
        "grand_total": grand_total
    })

#def has_permission(user_id, permission_name):
    #db = get_db()
    #cur = db.cursor()
#
    #cur.execute("""
    #    SELECT 1
    #    FROM user_permissions up
    #    JOIN permissions p ON up.permission_id = p.id
    #    WHERE up.user_id = %s AND p.name = %s
    #""", (user_id, permission_name))
#
    #allowed = cur.fetchone() is not None
    #cur.close()
    #db.close()
    #return allowed
    #return True;

@app.route("/folders", methods=["GET"])
def get_folders():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM product_folders ORDER BY created_at DESC")
    folders = cur.fetchall()
    cur.close()
    db.close()
    return jsonify(folders)

@app.route("/folders", methods=["POST"])
def create_folder():
    data = request.json
    if not data or "name" not in data:
        return jsonify({"error": "Folder name is required"}), 400
    
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO product_folders (name) VALUES (%s)", (data["name"],))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"message": "Folder created"}), 201
    


@app.route("/fields", methods=["GET"])
def get_fields():
    folder_id = request.args.get('folder_id')
    if not folder_id:
        return jsonify({"Error": "folder_id is required"}), 400
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM product_fields WHERE folder_id = %s", (folder_id,))
    fields = cur.fetchall()

    cur.close()
    db.close()
    return jsonify(fields)

@app.route("/fields", methods=["POST"])
def create_field():
    #if not has_permission(CURRENT_USER_ID, "MANAGE_FIELDS"):
      #  return jsonify({"error": "Permission denied"}), 403
    data = request.json

    if not data or "name" not in data or "type" not in data or "folder_id" not in data:
        return jsonify({"error": "name, type and folder_id required"}), 400
    
    db = get_db()
    cur = db.cursor()

    cur.execute(
        """
        INSERT INTO product_fields (field_name, field_type, is_required, folder_id)
        VALUES (%s, %s, %s, %s)
        """,
        (data["name"], data["type"], data.get("required", False), data["folder_id"])
    )

    db.commit()
    cur.close()
    db.close()
    return jsonify({"message": "Field created for folder"}), 201

@app.route("/products", methods=["POST"])
def create_product():
    #if not has_permission(CURRENT_USER_ID, "CREATE_PRODUCT"):
     #   return jsonify({"error": "Permission denied"}), 403
    data = request.json

    if not data or "name" not in data or "folder_id" not in data:
        return jsonify({"error": "Product name and fodler_id is required"}), 400

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "INSERT INTO products (name, folder_id) VALUES (%s, %s)",
        (data["name"], data["folder_id"])
    )
    product_id = cur.lastrowid

    for field_id, value in data.get("fields", {}).items():
        cur.execute(
            """
            INSERT INTO product_field_values
            (product_id, field_id, value)
            VALUES (%s, %s, %s)
            """,
            (product_id, field_id, value)
        )

    db.commit()
    cur.close()
    db.close()

    return jsonify({"id": product_id, "message": "Product created"}), 201


@app.route("/products", methods=["GET"])
def get_products():
    folder_id = request.args.get('folder_id')
    if not folder_id:
        return jsonify([])
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT p.id, p.name, f.field_name, v.value
        FROM products p
        LEFT JOIN product_field_values v ON p.id = v.product_id
        LEFT JOIN product_fields f ON v.field_id = f.id
        WHERE p.folder_id = %s
    """, (folder_id,))

    rows = cur.fetchall()
    products = {}

    for r in rows:
        pid = r["id"]
        if pid not in products:
            products[pid] = {
                "id": pid,
                "name": r["name"],
                "fields": {}
            }
        if r["field_name"]:
            products[pid]["fields"][r["field_name"]] = r["value"]

    cur.close()
    db.close()
    return jsonify(list(products.values()))

@app.route("/folders/<int:id>", methods=["PUT"])
def update_folder(id):
    data = request.json
    if not data or "name" not in data:
        return jsonify({"error": "Folder name is required"}), 400
    
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE product_folders SET name=%s WHERE id=%s", (data["name"], id))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"message": "Folder updated"})

@app.route("/folders/<int:id>", methods=["DELETE"])
def delete_folder(id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM product_folders WHERE id=%s", (id,))
    db.commit()
    cur.close()
    db.close()
    return jsonify({"message": "Folder deleted"})

@app.route("/products/<int:id>", methods=["PUT"])
def update_product(id):
    #if not has_permission(CURRENT_USER_ID, "UPDATE_PRODUCT"):
    #    return jsonify({"error": "Permission denied"}), 403
    data = request.json
    if not data or "name" not in data:
        return jsonify({"error": "Product name required"}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE products SET name=%s WHERE id=%s",
        (data["name"], id)
    )
    for field_id, value in data.get("fields", {}).items():
        cur.execute(
            """
            INSERT INTO product_field_values (product_id, field_id, value)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE value=%s
            """,
            (id, field_id, value, value)
        )
    db.commit()
    cur.close()
    db.close()
    return jsonify({"message": "Product updated"})

@app.route("/products/<int:id>", methods=["DELETE"])
def delete_product(id):
    #if not has_permission(CURRENT_USER_ID, "DELETE_PRODUCT"):
     #   return jsonify({"error": "Permission denied"}), 403
    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM products WHERE id=%s", (id,))
    db.commit()

    cur.close()
    db.close()
    return jsonify({"message": "Product deleted"})
#@app.route("/health/db", methods=["GET"])
#def db_health():
#    try:
#        db = get_db()
#        cur = db.cursor()
#        cur.execute("SELECT 1")
#        cur.fetchone()
#        cur.close()
#        db.close()
#        return jsonify({"db": "connected"}), 200
#    except Exception as e:
#        return jsonify({"db": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    print("Server is running.")