from functools import wraps
import logging

from flask import jsonify, request
from flask.views import MethodView
from sqlalchemy import select
from sqlalchemy.orm import joinedload
import firebase_admin
from firebase_admin import auth

from models import (
    db,
    Document,
    User,
    Domain,
    Number,
    Label,
    TypeEnum,
    ChangeControlledEnum,
    NumberConfirmationRequired,
    NumberGenerationError,
    OutOfOrderNumber,
    DRAWING_NUMBER_STEPS,
    get_entity,
    is_superuser
)

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


def _may_assign_document_number(entity, post_data):
    """
    Whether the caller is allowed to assign the number carried by post_data.

    Document numbers are admin only, so a non-superuser may only submit a
    document entry with no number. Drawing numbers are unaffected.

    Parameters
    ----------
    entity : User or Domain
        Entity the request was authenticated as.
    post_data : dict
        Payload of the create / update request.

    Returns
    -------
    bool
        True if the request may proceed, False if it must be rejected.
    """
    requests_number = bool(post_data.get("number") or post_data.get("confirmed_number"))
    is_document = post_data.get("entry_type") == TypeEnum.document.value

    if is_document and requests_number:
        return is_superuser(entity)
    return True


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
        entity = getattr(request, "entity")
        email = getattr(request, "email")
        response_object = {"status": "success"}
        logger.info(f"AllDocuments: User {email} is adding new document.")
        post_data = request.get_json()

        # If user is superuser, accept input value for creator_email
        if not is_superuser(entity):
            post_data["creator_email"] = email

        # Assigning a number to a document entry is superuser only. Drawings
        # keep their existing behaviour.
        if not _may_assign_document_number(entity, post_data):
            logger.info(
                f"AllDocuments: User {email} tried to assign a document number "
                "without superuser rights."
            )
            return jsonify(status="fail",
                           message="Only admins can assign document numbers"), 403

        # TODO need to check if this isn't a duplicate
        # TODO should validate fields
        try:
            success = Document.create(**post_data)
        except NumberConfirmationRequired as e:
            return jsonify(status="confirm", suggested_value=e.suggested_value,
                           message=str(e))
        except OutOfOrderNumber as e:
            return jsonify(status="out_of_order", suggested_next=e.suggested_next,
                           message=str(e))
        except NumberGenerationError as e:
            return jsonify(status="fail", message=str(e)), 400

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

        documents = (
            db.session.execute(
                select(Document)
                .options(
                    # Here 'joinedload' can be replaced by "selectinload"
                    # 'joinedload' is good if no duplicates (which should be out case),
                    # "selectinload" has better performance if duplicates
                    joinedload(Document.number),
                    joinedload(Document.aliases),
                    joinedload(Document.labels),
                )
                .order_by(Document.time_created.asc())
            )
            .unique()
            .scalars()
            .all()
        )

        response_object = {
            "status": "success",
            "documents": Document.serialize_list(documents),
            "superuser": is_superuser(entity),
        }
        return jsonify(response_object)


class AllNumbers(MethodView):
    """View class for the /documents route."""

    decorators = [token_required]

    def get(self):
        """
        Method with logic for get requests.
        Get requests here return a list of all the Numbers in the db.

        Returns
        -------
        json
            Json response to get request. Contains 'status' and a
            list of each document serialized.
        """
        entity = getattr(request, "entity")
        email = getattr(request, "email")
        logger.info(f"AllNumbers: User {email} is viewing all numbers.")

        numbers = (
            db.session.execute(
                select(Number)
                .options(
                    # Here 'joinedload' can be replaced by "selectinload"
                    # 'joinedload' is good if no duplicates (which should be out case), 
                    # "selectinload" has better performance if duplicates
                    joinedload(Number.document),
                    joinedload(Number.document).joinedload(Document.aliases),
                )
                .order_by(Number.time_created.desc())
            )
            .unique()
            .scalars()
            .all()
        )

        response_object = {
            "status": "success",
            "numbers": Number.serialize_list(numbers, max_depth=4),
            "superuser": is_superuser(entity),
        }
        return jsonify(response_object)


class EntryTypes(MethodView):
    """View class for the /entry_types route."""

    decorators = [token_required]
    # Map the entry types to Font Awesome icons
    ENTRY_TYPE_ICONS = {
        TypeEnum.document.value: "fa-solid fa-file-lines",
        TypeEnum.drawing.value: "fa-solid fa-compass-drafting",
        TypeEnum.other.value: "fa-solid fa-ellipsis",
    }

    def get(self):
        entry_types = [
            {"value": entry_type.value, "label": entry_type.name,
            "icon": self.ENTRY_TYPE_ICONS[entry_type.value]}
            for entry_type in TypeEnum
        ]
        return jsonify(entry_types=entry_types, default=Document.entry_type.default.arg.value)


class NumberSchemes(MethodView):
    """View class for the /number_schemes route."""

    decorators = [token_required]

    def get(self):
        """
        Method with logic for get requests.
        Get requests here return both numbering schemes, so that the client
        renders pickers from them instead of holding its own copy.

        Returns
        -------
        json
            Json response to get request. Contains 'status', the drawing tree
            steps and the list of document number stubs.
        """
        response = jsonify(
            status="success",
            drawing={"steps": DRAWING_NUMBER_STEPS},
            document={"stubs": Number.document_stubs()},
        )
        # The schemes change very rarely, so let the browser reuse them.
        response.headers["Cache-Control"] = "private, max-age=3600"
        return response


class ChangeControlledTypes(MethodView):
    """View class for the /change_controlled_types route."""

    decorators = [token_required]
    # Map the entry to style formatting
    ENTRY_CHANGE_CONTROLLED_TR_STYLE = {
        ChangeControlledEnum.no.value: "",
        ChangeControlledEnum.yes.value: "border-left: #6c757d solid 0.2em;",
    }

    def get(self):
        change_controlled_types = [
            {"value": change_controlled_type.value, "label": change_controlled_type.name,
            "tr_style": self.ENTRY_CHANGE_CONTROLLED_TR_STYLE[change_controlled_type.value]}
            for change_controlled_type in ChangeControlledEnum
        ]
        return jsonify(change_controlled_types=change_controlled_types, default=Document.change_controlled.default.arg.value)


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

    def get(self, doc_string):
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
        document = Document.get_by_doc_string(doc_string)
        if document:
            response_object["document"] = document.serialize()
        else:
            response_object["message"] = "No document found."
        return jsonify(response_object)

    def put(self, doc_string):
        """
        Method with logic for put requests.
        Put requests here update the column values for the document
        with given doc_identifier.

        Parameters
        ----------
        doc_string : str
            doc_identifier of document entry to be updated.

        Returns
        -------
        json
            Json response to put request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        entity = getattr(request, "entity")
        response_object = {"status": "success"}

        post_data = request.get_json()        
        document = Document.get_by_doc_string(doc_string)
        if document:
            if (document.creator_email != email) and (not entity.superuser):
                response_object['status'] = 'fail'
                response_object[
                    "message"
                ] = "User not authorized to update this document"
                logger.info(
                    f"SingleDocument: User {email} tried to update document they do not own."
                )
                return jsonify(response_object)

            logger.info(f"SingleDocument: User {email} is updating document.")

            # If user is superuser, accept input value for creator_email
            if not is_superuser(entity):
                post_data.pop("creator_email", None)

            # Assigning a number to a document entry is superuser only.
            if not _may_assign_document_number(entity, post_data):
                response_object["status"] = "fail"
                response_object["message"] = "Only admins can assign document numbers"
                logger.info(
                    f"SingleDocument: User {email} tried to assign a document "
                    "number without superuser rights."
                )
                return jsonify(response_object), 403

            try:
                success = document.update(**post_data)
            except NumberConfirmationRequired as e:
                return jsonify(status="confirm", suggested_value=e.suggested_value,
                               message=str(e))
            except OutOfOrderNumber as e:
                return jsonify(status="out_of_order", suggested_next=e.suggested_next,
                               message=str(e))
            except NumberGenerationError as e:
                return jsonify(status="fail", message=str(e)), 400

            if not success:
                response_object['status'] = 'fail'
            response_object["message"] = "Document updated!"
        else:
            logger.info(
                f"SingleDocument: User {email} tried to update inexistent document."
            )
            response_object["message"] = "Document not found"
        return jsonify(response_object)

    def delete(self, doc_string):
        """
        Method with logic for delete requests.
        Delete requests here delete document with given doc_identifier from the db.

        Parameters
        ----------
        doc_string : str
            doc_identifier of document entry to be deleted.

        Returns
        -------
        json
            Json response to delete request. Contains 'status' and 'message'.
        """
        email = getattr(request, "email")
        entity = getattr(request, "entity")
        response_object = {"status": "success"}

        document = Document.get_by_doc_string(doc_string)
        if document:
            if (document.creator_email != email) and (not entity.superuser):
                response_object['status'] = 'fail'
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
                response_object['status'] = 'fail'
            response_object["message"] = "Document removed!"
        else:
            logger.info(
                f"SingleDocument: User {email} tried to delete inexistent document."
            )
            response_object["message"] = "Document not found"
        return jsonify(response_object)


class AllLabels(MethodView):
    """View class for the /labels route."""

    decorators = [token_required]

    def post(self):
        """
        Method with logic for post requests.
        Post requests are made here when a superuser adds a new label.

        Returns
        -------
        json
            Json response to post request. Contains 'status' and 'message'.
        """
        entity = getattr(request, "entity")
        email = getattr(request, "email")
        response_object = {"status": "success"}

        if not is_superuser(entity):
            response_object["status"] = "fail"
            response_object["message"] = "Not authorized"
            logger.info(f"AllLabels: User {email} tried to add a label without superuser rights.")
            return jsonify(response_object), 403

        post_data = request.get_json()
        logger.info(f'AllLabels: User {email} is adding new label {post_data.get("name")}.')
        success = Label.create(**post_data)
        if not success:
            response_object["status"] = "fail"
        response_object["message"] = "Label added!"
        return jsonify(response_object)

    def get(self):
        """
        Method with logic for get requests.
        Get requests here return a list of all the labels in the db.

        Returns
        -------
        json
            Json response to get request. Contains 'status' and a
            list of each label serialized.
        """
        entity = getattr(request, "entity")
        email = getattr(request, "email")
        logger.info(f"AllLabels: User {email} is viewing all labels.")
        labels = db.session.scalars(select(Label).order_by(Label.name.asc()))

        response_object = {
            "status": "success",
            "labels": Label.serialize_list(labels),
            "superuser": is_superuser(entity),
        }
        return jsonify(response_object)


class SingleLabel(MethodView):
    """View class for the /labels/<pk> route."""

    decorators = [token_required]

    def put(self, pk):
        """
        Method with logic for put requests.
        Put requests here update the column values for the label with given
        private key.

        Parameters
        ----------
        pk : int / str
            pk of label entry to be updated.

        Returns
        -------
        json
            Json response to put request. Contains 'status' and 'message'.
        """
        entity = getattr(request, "entity")
        email = getattr(request, "email")
        response_object = {"status": "success"}

        if not is_superuser(entity):
            response_object["status"] = "fail"
            response_object["message"] = "Not authorized"
            logger.info(f"SingleLabel: User {email} tried to update a label without superuser rights.")
            return jsonify(response_object), 403

        post_data = request.get_json()
        label = Label.get_by_pk(pk)
        if label:
            logger.info(f"SingleLabel: User {email} is updating label {label}.")
            success = label.update(**post_data)
            if not success:
                response_object['status'] = 'fail'
            response_object["message"] = "Label updated!"
        else:
            logger.info(
                f"SingleLabel: User {email} tried to update inexistent label."
            )
            response_object["message"] = "Label not found"
        return jsonify(response_object)

    def delete(self, pk):
        """
        Method with logic for delete requests.
        Delete requests here delete label with given primary key from the db.

        Parameters
        ----------
        pk : int / str
            pk of label entry to be deleted.

        Returns
        -------
        json
            Json response to delete request. Contains 'status' and 'message'.
        """
        entity = getattr(request, "entity")
        email = getattr(request, "email")
        response_object = {"status": "success"}

        if not is_superuser(entity):
            response_object["status"] = "fail"
            response_object["message"] = "Not authorized"
            logger.info(f"SingleLabel: User {email} tried to delete a label without superuser rights.")
            return jsonify(response_object), 403

        label = Label.get_by_pk(pk)
        if label:
            logger.info(f"SingleLabel: User {email} is deleting label {label}.")
            success = label.delete_label()
            if not success:
                response_object['status'] = 'fail'
            response_object["message"] = "Label removed!"
        else:
            logger.info(
                f"SingleLabel: User {email} tried to delete inexistent label."
            )
            response_object["message"] = "Label not found"
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


class AllAdmins(MethodView):
    """View class for the /admins route."""

    decorators = [token_required]

    def get(self):
        """
        Method with logic for get requests.
        Get requests here return a list of all the admins in the db.

        Returns
        -------
        json
            Json response to get request. Contains 'status' and a
            list of each admin serialized.
        """
        email = getattr(request, "email")
        logger.info(f"AllUsers: User {email} is viewing all users.")
        admins = db.session.scalars(db.select(User).filter_by(superuser=True))
        admins = [a.email for a in admins]

        response_object = {
            "status": "success",
            "admins": admins,
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
                response_object['status'] = 'fail'
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
                response_object['status'] = 'fail'
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
                response_object['status'] = 'fail'
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
                response_object['status'] = 'fail'
            response_object["message"] = "Domain removed!"
        else:
            logger.info(
                f"SingleDomain: User {email} tried to delete inexistent domain."
            )
            response_object["message"] = "Domain not found"
        return jsonify(response_object)