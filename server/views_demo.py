import logging

from flask import jsonify, request
from flask.views import MethodView

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from models import is_superuser, TypeEnum, ChangeControlledEnum
from models_demo import (
    db,
    DemoDocument,
    DemoUser,
    DemoDomain,
    DemoNumber,
    NumberConfirmationRequired,
    OutOfOrderNumber,
)

from views import token_required, superuser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logger")


class DemoAllDocuments(MethodView):
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
        
        # TODO need to check if this isn't a duplicate
        # TODO should validate fields
        try:
            success = DemoDocument.create(**post_data)
        except NumberConfirmationRequired as e:
            return jsonify(status="confirm", suggested_value=e.suggested_value,
                           message=str(e))
        except OutOfOrderNumber as e:
            return jsonify(status="out_of_order", suggested_next=e.suggested_next,
                           message=str(e))

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
                select(DemoDocument)
                .options(
                    # Here 'joinedload' can be replaced by "selectinload"
                    # 'joinedload' is good if no duplicates (which should be out case), 
                    # "selectinload" has better performance if duplicates
                    joinedload(DemoDocument.number),
                    joinedload(DemoDocument.aliases),
                )
                .order_by(DemoDocument.time_created.asc())
            )
            .unique()
            .scalars()
            .all()
        )

        response_object = {
            "status": "success",
            "documents": DemoDocument.serialize_list(documents),
            "superuser": is_superuser(entity),
        }
        return jsonify(response_object)


class DemoAllNumbers(MethodView):
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
                select(DemoNumber)
                .options(
                    # Here 'joinedload' can be replaced by "selectinload"
                    # 'joinedload' is good if no duplicates (which should be out case), 
                    # "selectinload" has better performance if duplicates
                    joinedload(DemoNumber.document),
                    joinedload(DemoNumber.document).joinedload(DemoDocument.aliases),
                )
                .order_by(DemoNumber.time_created.desc())
            )
            .unique()
            .scalars()
            .all()
        )

        response_object = {
            "status": "success",
            "numbers": DemoNumber.serialize_list(numbers, max_depth=4),
            "superuser": is_superuser(entity),
        }
        return jsonify(response_object)


class DemoEntryTypes(MethodView):
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
        return jsonify(entry_types=entry_types, default=DemoDocument.entry_type.default.arg.value)


class DemoChangeControlledTypes(MethodView):
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
        return jsonify(change_controlled_types=change_controlled_types, default=DemoDocument.change_controlled.default.arg.value)


class DemoUploadFile(MethodView):
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
                kwargs = DemoDocument.prepare_fields(**post_data)

                # Don't break upload, just skip the duplicated entry
                if DemoDocument.duplicate_exists(**kwargs):
                    continue

                obj = DemoDocument(**kwargs)
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


class DemoSingleDocument(MethodView):
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
        document = DemoDocument.get_by_doc_string(doc_string)
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
        document = DemoDocument.get_by_doc_string(doc_string)
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
            
            try:
                success = document.update(**post_data)
            except NumberConfirmationRequired as e:
                return jsonify(status="confirm", suggested_value=e.suggested_value,
                               message=str(e))
            except OutOfOrderNumber as e:
                return jsonify(status="out_of_order", suggested_next=e.suggested_next,
                               message=str(e))

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

        document = DemoDocument.get_by_doc_string(doc_string)
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


class DemoAllUsers(MethodView):
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
        success = DemoUser.create(**post_data)
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
        users = db.session.scalars(db.select(DemoUser))

        # from flask import request

        response_object = {
            "status": "success",
            "collaborators": DemoUser.serialize_list(users),
            "superuser": is_superuser(entity),
        }
        return jsonify(response_object)


class DemoAllAdmins(MethodView):
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
        admins = db.session.scalars(db.select(DemoUser).filter_by(superuser=True))
        admins = [a.email for a in admins]

        response_object = {
            "status": "success",
            "admins": admins,
        }
        return jsonify(response_object)


class DemoSingleUser(MethodView):
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
        user_to_update = DemoUser.get_by_pk(pk)
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

        user = DemoUser.get_by_pk(pk)
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


class DemoAllDomains(MethodView):
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
        success = DemoDomain.create(**post_data)
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
        domains = db.session.scalars(db.select(DemoDomain))

        response_object = {
            "status": "success",
            "domains": DemoUser.serialize_list(domains),
            "superuser": is_superuser(entity),
        }
        return jsonify(response_object)


class DemoSingleDomain(MethodView):
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
        domain = DemoDomain.get_by_pk(pk)
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

        domain = DemoDomain.get_by_pk(pk)
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
