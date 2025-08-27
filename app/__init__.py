<<<<<<< HEAD
# -*- coding: utf-8 -*-

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .models import db
=======
from flask import Flask
import os

>>>>>>> 113f45e4c4adce49a832eacd2d33dc61e112a042
from .routes import app_routes

def create_app():
    app = Flask(__name__)

<<<<<<< HEAD
    # --- CONFIGURATION SÉCURISÉE ---
    
    # On récupère les valeurs depuis les variables d'environnement
    db_uri = os.environ.get('DATABASE_URL')
    secret = os.environ.get('SECRET_KEY')

    # On vérifie que les variables existent BIEN AVANT de configurer l'app
    if not db_uri:
        raise ValueError("Erreur : La variable d'environnement DATABASE_URL n'est pas définie dans votre fichier .env ou sur le serveur.")
    if not secret:
        raise ValueError("Erreur : La variable d'environnement SECRET_KEY n'est pas définie dans votre fichier .env ou sur le serveur.")

    # On configure l'application avec les valeurs vérifiées
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SECRET_KEY'] = secret
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialisation des extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Enregistrer les blueprints
    app.register_blueprint(app_routes)

    return app
=======
    # Set the secret key (use an environment variable for security)
    app.secret_key = os.environ.get("SECRET_KEY", "112233")  # Set it here

    @app.route("/")
    def home():
        return "Welcome to the Web App! Go to /students to see the student page."

    app.register_blueprint(app_routes)

    return app
>>>>>>> 113f45e4c4adce49a832eacd2d33dc61e112a042
