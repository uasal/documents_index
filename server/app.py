from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

import logging

logger = logging.getLogger('logger')

db = SQLAlchemy()

def create_app():
    # instantiate the app
    logger.info('Instantiating Flask app.')
    app = Flask(__name__)
    app.config.from_object(__name__)

    logger.info('Instantiating db with Flask app.')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///docs.db'
    db.init_app(app) # init of db is deferred

    # If no database exists, set to True to create database tables
    CREATE_TABLES = False
    if CREATE_TABLES:
        with app.app_context():
            from models import Document # noqa: F401; All models need to be imported for db.create_all() to create relevat tables
            logger.info('CREATE_TABLES flag set to True - creating new database.')
            db.create_all()

    # enable CORS (needed for Vue)
    logger.info('Enabling CORS.')
    CORS(app, resources={r'/*': {'origins': '*'}})

    # register views
    from views import Ping, AllDocuments, SingleDocument
    logger.info('Registering views.')
    app.add_url_rule("/api/pong", view_func=Ping.as_view("ping"))
    app.add_url_rule("/api/documents", view_func=AllDocuments.as_view("document_list"))
    app.add_url_rule("/api/documents/<doc_identifier>", 
                     view_func=SingleDocument.as_view("single_document"))
    return app

app = create_app()

if __name__ == '__main__':
    logger.info('Starting app.')
    app.run()
