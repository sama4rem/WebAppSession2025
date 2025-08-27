# -*- coding: utf-8 -*-

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .models import db
from .routes import app_routes

def create_app():
    app = Flask(__name__)

    # --- SÉCURISATION DE LA CONFIGURATION ---
    
    # Récupérer les valeurs des variables d'environnement
    db_uri = os.environ.get('DATABASE_URL')
    secret = os.environ.get('SECRET_KEY')

    # Vérifier que les variables existent avant de configurer l'app
    if not db_uri:
        raise ValueError("Erreur : La variable d'environnement DATABASE_URL n'est pas définie.")
    if not secret:
        raise ValueError("Erreur : La variable d'environnement SECRET_KEY n'est pas définie.")

    # Configurer l'application avec les valeurs vérifiées
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SECRET_KEY'] = secret
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialisation des extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Enregistrer les blueprints
    app.register_blueprint(app_routes)

    return app