from functools import wraps
import logging

from flask import jsonify, request
from flask.views import MethodView
import firebase_admin
from firebase_admin import auth

from models import db, Document, User, Domain, get_entity, is_superuser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logger")


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            firebase_admin.get_app()
        except Exception as e:
            firebase_admin.initialize_app()

        token = request.headers.get("Authorization")

        if token:
            logger.info("TokenRequired: Extracted token.")

            try:
                # decoded_token = auth.verify_id_token(token, check_revoked=True)
                decoded_token = auth.verify_id_token(token)
            except Exception as e:
                logger.error(
                    f"TokenRequired: Error in decoding user token:\nmessage: {e}\n"
                )
                return {
                    "status": "fail",
                    "message": "Resource not available",
                    "isAuthorized": False,
                }, 401
            else:
                logger.info("TokenRequired: Token successfully decoded")
                setattr(request, "decoded_token", decoded_token)

                email = decoded_token.get("email")
                setattr(request, "email", email)

                entity = get_entity(email)
                if not entity:
                    return {
                        "status": "fail",
                        "message": "Not authorized",
                        "isAuthorized": False,
                    }, 401
                setattr(request, "entity", entity)

                return f(*args, **kwargs)

        logger.error("TokenRequired: No token found with request.")
        return {
            "status": "fail",
            "message": "Resource not available",
            "isAuthorized": False,
        }, 401

    return decorated_function


def superuser(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        entity = getattr(request, "entity")

        if not is_superuser(entity):
            return {
                "status": "fail",
                "message": "Not authorized",
                "isSuperuser": False,
            }, 403
        return f(*args, **kwargs)

    return decorated_function


# sanity check route
class Ping(MethodView):
    def get(self):
        logger.info("Pong!")
        return jsonify("pong!")


class AllDocuments(MethodView):
    """View class for the /documents route."""

    decorators = [token_required]

    def post(self):
        """
        Method with logic for post requests.
        Post requests are made here when the user adds a new document.

        Returns
        -------
        json
            Json response to post request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        response_object = {"status": "success"}
        logger.info(f"AllDocuments: User {email} is adding new document.")
        post_data = request.get_json()
        post_data["creator_email"] = email
        # TODO need to check if this isn't a duplicate
        # TODO should validate fields
        success = Document.create(**post_data)
        if not success:
            response_object["status"] = "fail"
        response_object["message"] = "Document added!"
        return jsonify(response_object)

    def get(self):
        """
        Method with logic for get requests.
        Get requests here return a list of all the documents in the db.

        Returns
        -------
        json
            Json response to get request. Contains 'status' and a
            list of each document serialized.
        """
        entity = getattr(request, "entity")
        email = getattr(request, "email")
        logger.info(f"AllDocuments: User {email} is viewing all documents.")
        documents = db.session.scalars(db.select(Document))

        response_object = {
            "status": "success",
            "documents": Document.serialize_list(documents),
            "superuser": is_superuser(entity),
        }
        return jsonify(response_object)


class UploadFile(MethodView):
    """View class for the /documents/upload_file route."""

    decorators = [token_required]

    def post(self):
        """
        Method with logic for post requests.
        Post requests are made here when the user uploads a file with
        metadata for documents.

        Returns
        -------
        json
            Json response to post request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        response_object = {"status": "success"}
        logger.info(f"UploadFile: User {email} is uploading a file.")

        file = request.files["file"]
        if "text" not in file.content_type:
            response_object["status"] = "fail"
            return jsonify(response_object)

        lines = []
        nb_columns = 6
        for bline in file.stream.readlines():
            line = bline.decode()

            if line.strip()[0] != "#":
                columns = line.split("|")

                if len(columns) != nb_columns:
                    response_object["status"] = "fail"
                    return jsonify(response_object)

                lines.append(columns)

        try:
            for line in lines:
                post_data = {
                    "title": line[0].strip().strip("\n").strip(),
                    "author": line[1].strip().strip("\n").strip(),
                    "doc_code": line[2].strip().strip("\n").strip(),
                    "compiled_url": line[3].strip().strip("\n").strip(),
                    "source_url": line[4].strip().strip("\n").strip(),
                    "abstract": line[5].strip().strip("\n").strip(),
                    "creator_email": email,
                }
                kwargs = Document.prepare_fields(**post_data)

                # Don't break upload, just skip the duplicated entry
                if Document.duplicate_exists(**kwargs):
                    continue

                obj = Document(**kwargs)
                db.session.add(obj)

            logger.info(f"UploadFile: User {email} adding new documents from file.")
            db.session.commit()
        except Exception as e:
            logger.error(
                f"UploadFile: User {email} tried adding new"
                f"documents from file. Errror: {e}"
            )
            response_object["status"] = "fail"

        response_object["message"] = "Document added!"
        return jsonify(response_object)


class SingleDocument(MethodView):
    """View class for the /documents/<document_id> route."""

    decorators = [token_required]

    def get(self, doc_identifier):
        """
        Method with logic for get requests.
        Get requests here returns details for document with given document id.

        Parameters
        ----------
        document_id : int / str
            Id of document entry to be updated.

        Returns
        -------
        json
            Json response to get request. Contains serialized Document object
            with given document id.
        """
        entity = getattr(request, "entity")
        email = getattr(request, "email")
        logger.info(f"AllDocuments: User {email} is viewing all documents.")
        response_object = {"status": "success", "superuser": is_superuser(entity)}
        document = Document.get_by_doc_identifier(doc_identifier)
        if document:
            response_object["document"] = document.serialize()
        else:
            response_object["message"] = "No document found."
        return jsonify(response_object)

    def put(self, doc_identifier):
        """
        Method with logic for put requests.
        Put requests here update the column values for the document
        with given doc_identifier.

        Parameters
        ----------
        doc_identifier : str
            doc_identifier of document entry to be updated.

        Returns
        -------
        json
            Json response to put request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        response_object = {"status": "success"}

        post_data = request.get_json()
        document = Document.get_by_doc_identifier(doc_identifier)
        if document:
            if document.creator_email != email:
                response_object["status":"fail"]
                response_object[
                    "message"
                ] = "User not authorized to update this document"
                logger.info(
                    f"SingleDocument: User {email} tried to update document they do not own."
                )
                return jsonify(response_object)

            logger.info(f"SingleDocument: User {email} is updating document.")
            success = document.update(**post_data)
            if not success:
                response_object["status":"fail"]
            response_object["message"] = "Document updated!"
        else:
            logger.info(
                f"SingleDocument: User {email} tried to update inexistent document."
            )
            response_object["message"] = "Document not found"
        return jsonify(response_object)

    def delete(self, doc_identifier):
        """
        Method with logic for delete requests.
        Delete requests here delete document with given doc_identifier from the db.

        Parameters
        ----------
        doc_identifier : str
            doc_identifier of document entry to be deleted.

        Returns
        -------
        json
            Json response to delete request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        response_object = {"status": "success"}

        document = Document.get_by_doc_identifier(doc_identifier)
        if document:
            if document.creator_email != email:
                response_object["status":"fail"]
                response_object[
                    "message"
                ] = "User not authorized to delete this document"
                logger.info(
                    f"SingleDocument: User {email} tried to delete document they do not own."
                )
                return jsonify(response_object)

            logger.info(f"SingleDocument: User {email} is deleting document.")
            success = document.delete_doc()
            if not success:
                response_object["status":"fail"]
            response_object["message"] = "Document removed!"
        else:
            logger.info(
                f"SingleDocument: User {email} tried to delete inexistent document."
            )
            response_object["message"] = "Document not found"
        return jsonify(response_object)


class AllUsers(MethodView):
    """View class for the /users route."""

    decorators = [superuser, token_required]

    def post(self):
        """
        Method with logic for post requests.
        Post requests are made here when the user adds a new user.

        Returns
        -------
        json
            Json response to post request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        response_object = {"status": "success"}
        post_data = request.get_json()
        logger.info(
            f'AllUsers: User {email} is adding new user {post_data.get("email")}.'
        )
        success = User.create(**post_data)
        if not success:
            response_object["status"] = "fail"
        response_object["message"] = "User added!"
        return jsonify(response_object)

    def get(self):
        """
        Method with logic for get requests.
        Get requests here return a list of all the users in the db.

        Returns
        -------
        json
            Json response to get request. Contains 'status' and a
            list of each user serialized.
        """
        entity = getattr(request, "entity")
        email = getattr(request, "email")
        logger.info(f"AllUsers: User {email} is viewing all users.")
        users = db.session.scalars(db.select(User))

        # from flask import request

        response_object = {
            "status": "success",
            "collaborators": User.serialize_list(users),
            "superuser": is_superuser(entity),
        }
        return jsonify(response_object)


class SingleUser(MethodView):
    """View class for the /users/<pk> route."""

    decorators = [superuser, token_required]

    def put(self, pk):
        """
        Method with logic for put requests.
        Put requests here update the column values for the user with given
        private key.

        Parameters
        ----------
        pk : int / str
            pk of user entry to be updated.

        Returns
        -------
        json
            Json response to put request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        response_object = {"status": "success"}

        post_data = request.get_json()
        user_to_update = User.get_by_pk(pk)
        if user_to_update:
            logger.info(f"SingleUser: User {email} is updating user {user_to_update}.")
            success = user_to_update.update(**post_data)
            if not success:
                response_object["status":"fail"]
            response_object["message"] = "User updated!"
        else:
            logger.info(
                f"SingleDocument: User {email} tried to update inexistent "
                f"user {user_to_update}."
            )
            response_object["message"] = "User not found"
        return jsonify(response_object)

    def delete(self, pk):
        """
        Method with logic for delete requests.
        Delete requests here delete user with given primary key from the db.

        Parameters
        ----------
        pk : int / str
            pk of user entry to be deleted.

        Returns
        -------
        json
            Json response to delete request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        response_object = {"status": "success"}

        user = User.get_by_pk(pk)
        if user:
            logger.info(f"SingleUser: User {email} is deleting user {user.email}.")
            success = user.delete_user()
            if not success:
                response_object["status":"fail"]
            response_object["message"] = "User removed!"
        else:
            logger.info(f"SingleUser: User {email} tried to delete inexistent user.")
            response_object["message"] = "User not found"
        return jsonify(response_object)


class AllDomains(MethodView):
    """View class for the /domains route."""

    decorators = [superuser, token_required]

    def post(self):
        """
        Method with logic for post requests.
        Post requests are made here when the user adds a new domain.

        Returns
        -------
        json
            Json response to post request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        response_object = {"status": "success"}
        post_data = request.get_json()
        logger.info(
            f'AllDomains: User {email} is adding new domain {post_data.get("email_domain")}.'
        )
        success = Domain.create(**post_data)
        if not success:
            response_object["status"] = "fail"
        response_object["message"] = "Domain added!"
        return jsonify(response_object)

    def get(self):
        """
        Method with logic for get requests.
        Get requests here return a list of all the domains in the db.

        Returns
        -------
        json
            Json response to get request. Contains 'status' and a
            list of each domain serialized.
        """
        entity = getattr(request, "entity")
        email = getattr(request, "email")
        logger.info(f"AllDomains: User {email} is viewing all domains.")
        domains = db.session.scalars(db.select(Domain))

        response_object = {
            "status": "success",
            "domains": User.serialize_list(domains),
            "superuser": is_superuser(entity),
        }
        return jsonify(response_object)


class SingleDomain(MethodView):
    """View class for the /domains/<pk> route."""

    decorators = [superuser, token_required]

    def put(self, pk):
        """
        Method with logic for put requests.
        Put requests here update the column values for the domain with given
        private key.

        Parameters
        ----------
        pk : int / str
            pk of domain entry to be updated.

        Returns
        -------
        json
            Json response to put request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        response_object = {"status": "success"}

        post_data = request.get_json()
        domain = Domain.get_by_pk(pk)
        if domain:
            logger.info(f"SingleDomain: User {email} is updating domain {domain}.")
            success = domain.update(**post_data)
            if not success:
                response_object["status":"fail"]
            response_object["message"] = "Domain updated!"
        else:
            logger.info(
                f"SingleDomain: User {email} tried to update inexistent domain {domain}."
            )
            response_object["message"] = "Domain not found"
        return jsonify(response_object)

    def delete(self, pk):
        """
        Method with logic for delete requests.
        Delete requests here delete domain with given primary key from the db.

        Parameters
        ----------
        pk : int / str
            pk of domain entry to be deleted.

        Returns
        -------
        json
            Json response to delete request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        response_object = {"status": "success"}

        domain = Domain.get_by_pk(pk)
        if domain:
            logger.info(f"SingleDomain: User {email} is deleting domain {domain}.")
            success = domain.delete_domain()
            if not success:
                response_object["status":"fail"]
            response_object["message"] = "Domain removed!"
        else:
            logger.info(
                f"SingleDomain: User {email} tried to delete inexistent domain."
            )
            response_object["message"] = "Domain not found"
        return jsonify(response_object)
