<<<<<<< HEAD
# Fichier run.py - Version simple et correcte

from app import create_app
from dotenv import load_dotenv

# Charge les variables du fichier .env dans l'environnement
# C'est la PREMIÈRE chose à faire
load_dotenv()

# Crée l'instance de l'application. La fonction create_app() lira les variables
# que load_dotenv() vient de charger.
app = create_app()

if __name__ == '__main__':
    # Lance l'application pour le développement local
    # Flask utilisera le port 5000 par défaut
    app.run(debug=True)
=======
from app import create_app
import os

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Set a secret key for sessions (best practice: use environment variable)
    app.secret_key = os.environ.get("SECRET_KEY", "555555")

    # Get the port from Render (default to 10000 if not found)
    port = int(os.environ.get("PORT", 10000))

    # Run the app on 0.0.0.0 to accept external requests
    app.run(host="0.0.0.0", port=port)
>>>>>>> 113f45e4c4adce49a832eacd2d33dc61e112a042
