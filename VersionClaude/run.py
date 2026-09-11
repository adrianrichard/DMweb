import os
from dotenv import load_dotenv

load_dotenv()  # lee el archivo .env de la raíz del proyecto, si existe

from app import create_app

app = create_app(os.environ.get("FLASK_CONFIG", "development"))

if __name__ == "__main__":
    app.run()
