from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# import ssl
import logging

# from database import DB_URI, CERT_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logger")

db = SQLAlchemy()


def create_app():
    # instantiate the app
    logger.info("Instantiating Flask app.")
    app = Flask(__name__)
    app.config.from_object(__name__)

    logger.info("Instantiating db with Flask app.")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///docs.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI

    # ssl_context = ssl.create_default_context()
    # ssl_context.verify_mode = ssl.CERT_REQUIRED
    # ssl_context.load_verify_locations(CERT_PATH)
    # app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    #     "connect_args": {"ssl_context": ssl_context}
    # }

    db.init_app(app)  # init of db is deferred

    # If no database exists, set to True to create database tables
    CREATE_TABLES = False
    if CREATE_TABLES:
        with app.app_context():
            from models import Document  # noqa: F401; All models need to be imported for db.create_all() to create relevat tables

            logger.info("CREATE_TABLES flag set to True - creating new database.")
            db.create_all()

    # enable CORS (needed for Vue)
    logger.info("Enabling CORS.")
    CORS(app, resources={r"/*": {"origins": "*"}})
    # CORS(app, resources={r"/*": {"origins": "https://dis-6bnmqttxma-uc.a.run.app"}})

    # register views
    from views import (
        Ping,
        AllDocuments,
        UploadFile,
        SingleDocument,
        AllUsers,
        AllAdmins,
        SingleUser,
        AllDomains,
        SingleDomain,
    )

    logger.info("Registering views.")
    app.add_url_rule("/api/pong", view_func=Ping.as_view("ping"))
    app.add_url_rule("/api/documents", view_func=AllDocuments.as_view("document_list"))
    app.add_url_rule(
        "/api/documents/upload_file", view_func=UploadFile.as_view("upload_file")
    )
    app.add_url_rule(
        "/api/documents/<doc_identifier>",
        view_func=SingleDocument.as_view("single_document"),
    )
    app.add_url_rule("/api/users", view_func=AllUsers.as_view("user_list"))
    app.add_url_rule("/api/users/<pk>", view_func=SingleUser.as_view("single_user"))
    app.add_url_rule("/api/admins", view_func=AllAdmins.as_view("admin_list"))
    app.add_url_rule("/api/domains", view_func=AllDomains.as_view("domain_list"))
    app.add_url_rule(
        "/api/domains/<pk>", view_func=SingleDomain.as_view("single_domain")
    )
    return app


app = create_app()

with app.app_context():
    from models import User, db

    nb_users = User.query.count()
    logger.info(f"HERE::::: {nb_users} users")

if __name__ == "__main__":
    logger.info("Starting app.")
    app.run()
