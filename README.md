# Inventario PaaS

Aplicación web mínima de inventario (Flask + SQLite) para la práctica de PaaS.

## Ejecución local
```bash
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                   # http://localhost:5000
```

## Endpoints
| Método | Ruta | Descripción |
|---|---|---|
| GET | / | Interfaz web |
| GET | /health | Estado del servicio |
| GET | /api/productos | Listar |
| POST | /api/productos | Crear |
| PUT | /api/productos/<id> | Editar |
| DELETE | /api/productos/<id> | Eliminar |

## Despliegue en Render
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Variables de entorno: `APP_NAME`, `APP_ENV=produccion`, `PYTHON_VERSION=3.12.3`
