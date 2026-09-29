import logging
import os
import sqlite3

from flask import Flask, g, jsonify, render_template, request

# --- Variables de configuración (se definen en la plataforma PaaS) ---
APP_NAME = os.environ.get("APP_NAME", "Inventario PaaS")
APP_ENV = os.environ.get("APP_ENV", "desarrollo")
DB_PATH = os.environ.get("DB_PATH", "inventario.db")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)
log = app.logger


# --- Base de datos ---
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 0,
                precio REAL NOT NULL DEFAULT 0
            )"""
        )


init_db()


def validar(datos):
    """Devuelve (datos_limpios, error)."""
    if not datos:
        return None, "Se esperaba un JSON"
    nombre = str(datos.get("nombre", "")).strip()
    if not nombre:
        return None, "El nombre es obligatorio"
    try:
        cantidad = int(datos.get("cantidad", 0))
        precio = float(datos.get("precio", 0))
    except (TypeError, ValueError):
        return None, "Cantidad y precio deben ser numéricos"
    if cantidad < 0 or precio < 0:
        return None, "Cantidad y precio no pueden ser negativos"
    return {"nombre": nombre, "cantidad": cantidad, "precio": precio}, None


# --- Rutas ---
@app.route("/")
def index():
    return render_template("index.html", app_name=APP_NAME, app_env=APP_ENV)


@app.route("/health")
def health():
    return jsonify(estado="ok", entorno=APP_ENV)


@app.route("/api/productos", methods=["GET"])
def listar():
    filas = get_db().execute("SELECT * FROM productos ORDER BY id").fetchall()
    return jsonify([dict(f) for f in filas])


@app.route("/api/productos", methods=["POST"])
def crear():
    datos, error = validar(request.get_json(silent=True))
    if error:
        log.warning("Creación rechazada: %s", error)
        return jsonify(error=error), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO productos (nombre, cantidad, precio) VALUES (?, ?, ?)",
        (datos["nombre"], datos["cantidad"], datos["precio"]),
    )
    db.commit()
    log.info("Producto creado id=%s nombre=%s", cur.lastrowid, datos["nombre"])
    return jsonify(id=cur.lastrowid, **datos), 201


@app.route("/api/productos/<int:pid>", methods=["PUT"])
def editar(pid):
    datos, error = validar(request.get_json(silent=True))
    if error:
        log.warning("Edición rechazada id=%s: %s", pid, error)
        return jsonify(error=error), 400
    db = get_db()
    cur = db.execute(
        "UPDATE productos SET nombre=?, cantidad=?, precio=? WHERE id=?",
        (datos["nombre"], datos["cantidad"], datos["precio"], pid),
    )
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="Producto no encontrado"), 404
    log.info("Producto editado id=%s", pid)
    return jsonify(id=pid, **datos)


@app.route("/api/productos/<int:pid>", methods=["DELETE"])
def eliminar(pid):
    db = get_db()
    cur = db.execute("DELETE FROM productos WHERE id=?", (pid,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="Producto no encontrado"), 404
    log.info("Producto eliminado id=%s", pid)
    return "", 204


if __name__ == "__main__":
    # Solo para pruebas locales. En el PaaS se usa gunicorn.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=(APP_ENV == "desarrollo"))
