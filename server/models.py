import re
import enum

from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy.inspection import inspect
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import validates
from sqlalchemy.types import TypeDecorator
from app import db

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logger")


class Serializer(object):
    """A mix-in to serialize SQLAlchemy models."""

    def serialize(self, depth=0, max_depth=2):
        """
        Serializes a single model object.

        Returns
        -------
        dict
            A dictionary with object's column names as keys and values as values
        """
        serialized = {}

        if depth < max_depth:
            for c in inspect(self).attrs.keys():
                match value := getattr(self, c):
                    case enum.Enum():
                        serialized[c] = value.value

                    case list():
                        serialized[c] = self.serialize_list(value, depth+1, max_depth)

                    case db.Model():
                        serialized[c] = value.serialize(depth+1, max_depth)

                    case _:
                        serialized[c] = value
        else:
            serialized["pk"] = self.pk

        return serialized

    @staticmethod
    def serialize_list(obj_list, depth=0, max_depth=2):
        """
        Given a list of model objects returns a list with the objects serialized.

        Parameters
        ----------
        l : list
            List of model objects

        Returns
        -------
        list
            List of serialized objects
        """
        return [m.serialize(depth, max_depth) for m in obj_list]


class TypeEnum(enum.Enum):
    document = "document"
    drawing = "drawing"
    other = "other"

class ChangeControlledEnum(enum.Enum):
    no = 0
    yes = 10

    @classmethod
    def __contains__(cls, item):
        """
        Magic method that checks whether there is a ChangeControlledEnum entry associated with
        given item.

        Parameters
        ----------
        item : int
            Integer to be checked against ChangeControlledEnum entries.

        Returns
        -------
        bool
            Whether there exists or not a ChangeControlledEnum entry for the given item.
        """
        try:
            cls(item)
        except ValueError:
            return False
        else:
            return True


class ChangeControlledType(TypeDecorator):
    """
    Custom TypeDecorator to store the enum as an integer in the database
    """

    # Underlying column type
    impl = db.Integer

    def process_bind_param(self, value, dialect):
        """
        From SQLAlchemy docs:
        `Custom subclasses of TypeDecorator override this method to define custom behaviors
        for incoming data values. This method is called at statement execution time and is 
        passed the literal Python data value which is to be associated with a bound parameter 
        in the statement.`

        In this case, checking that the value is valid for the enum before storing it in database.
        If not a valid value, fallback to default value.

        Parameters
        ----------
        value : int
            Integer associated with value in ChangeControlledEnum.
        dialect: sqlalchemy.engine.Dialect
            The sqlalchemy Dialect in use.

        Returns
        -------
        int
            Integer associated with value in ChangeControlledEnum.
        """
        return value if ChangeControlledEnum.__contains__(value) else Document.change_controlled.default.arg.value

    def process_result_value(self, value, dialect):
        """
        From SQLAlchemy docs:
        `Custom subclasses of TypeDecorator override this method to define custom behaviors
        for incoming data values. This method is called at statement execution time and is 
        passed the literal Python data value which is to be associated with a bound parameter 
        in the statement.`

        In this case, convert the integer back to the enum when querying.
        If not a valid value, return None

        Parameters
        ----------
        value : int
            Integer associated with value in ChangeControlledEnum.
        dialect: sqlalchemy.engine.Dialect
            The sqlalchemy Dialect in use.

        Returns
        -------
        ChangeControlledEnum or None
            ChangeControlledEnum associated with integer.
        """
        try:
            return ChangeControlledEnum(value) if value is not None else None
        except ValueError:
            return None


class NumberConfirmationRequired(Exception):
    """Raised when a user-specified drawing number exists and confirmation is required.

    Attributes:
        suggested_value: a full suggested value including incremented config (e.g. 'ABC-DE001-01')
    """
    def __init__(self, suggested_value, message=None):
        super().__init__(message or "Number confirmation required")
        self.suggested_value = suggested_value


class OutOfOrderNumber(Exception):
    """Raised when a user-specified drawing number is out of sequence.

    Attributes:
        suggested_next: a suggested next-in-sequence value (e.g. 'ABC-DE002-00')
    """
    def __init__(self, suggested_next, message=None):
        super().__init__(message or "Out of order number")
        self.suggested_next = suggested_next

class Document(db.Model, Serializer):
    """
    Document model class to act as interface between the Flask logic and the
    sql table.
    """

    pk = db.Column("pk", db.Integer, primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    title = db.Column("title", db.String(500), nullable=False)
    author = db.Column("author", db.String(500), nullable=False)
    doc_identifier = db.Column("doc_identifier", db.String(20), nullable=False)
    # doc_code = db.Column("doc_code", db.String(30), default="")
    compiled_url = db.Column("compiled_url", db.String(500), default="")
    source_url = db.Column("source_url", db.String(500), default="")
    abstract = db.Column("abstract", db.Text, default="")
    creator_email = db.Column("creator_email", db.String(100), nullable=False)
    entry_type = db.Column("entry_type", db.Enum(TypeEnum), default=TypeEnum.document, nullable=False)
    change_controlled = db.Column("change_controlled", ChangeControlledType, default=ChangeControlledEnum.no, nullable=False)

    # Relationship to Number
    number = db.relationship("Number", back_populates="document", uselist=False)

    # Relationship to Alias
    aliases = db.relationship("Alias", back_populates="document")


    def __repr__(self):
        """
        Magic method that returns the string representation of the Document model.

        Returns
        -------
        str
            String representation of the Document model.
        """
        return "<Document %r>" % self.title

    def _get_editable_columns(self):
        """
        Private method to return a list of the model's editable columns.

        Returns
        -------
        list
            List of the model's editable columns
        """
        columns = inspect(self).attrs.keys()
        return list(
            set(columns) - set(["time_created", "time_updated", "doc_identifier", "number", "aliases"])
        )

    def _get_all_columns(self):
        """
        Private method to return a list of all the model's columns.

        Returns
        -------
        list
            List of all the model's columns
        """
        return inspect(self).attrs.keys()

    @staticmethod
    def _check_http(val):
        # Guard against null value
        if val is None:
            val = ""

        val = val.strip()
        if val.startswith("http"):
            return val
        elif val:
            return f"https://{val}"
        else:
            return ""

    def update(self, **kwargs):
        """
        Method to update an existing object's column values with those in the
        kwargs.

        Returns
        -------
        bool
            Returns True is update was successful and False if an error was
            encountered.
        """
        columns = self._get_editable_columns()
        try:
            for column in columns:
                new_val = kwargs.get(column, None)

                if column in ["compiled_url", "source_url"]:
                    new_val = self._check_http(new_val)

                if new_val is not None:
                    setattr(self, column, new_val)
            self._update_number(kwargs.get("change_controlled"), 
                                kwargs.get("entry_type"), 
                                kwargs.get("number"),
                                kwargs.get("confirmed_number"))
            db.session.add(self)
            db.session.commit()
            logger.info("Documents: Updating Document object.")
        except (NumberConfirmationRequired, OutOfOrderNumber):
            # Let caller (views) handle confirmation / out-of-order flows
            raise
        except Exception as e:
            logger.error(f"Documents: Updating Document object. Error: {e}")
            return False
        return True

    def _update_number(self, change_controlled, entry_type, user_value, confirmed_number=None):
        """
        Class method to check if entry to be updated already has a linked
        Number (in which case, validate that it matches the criteria) or not
        (in which case, trigger generation method).

        Parameters
        ----------
        change_controlled :
            value of Document object's change_controlled field
        entry_type :
            value of Document object's entry_type field
        user_value :
            user provided value; can be empty string

        Returns
        -------
        Bool or Number object
            If criteria for creating Number object are met, object is created and 
            returned, otherwise returns bool.

        Raises
        ------
        ValueError
            Exception raised if document already exists in the db with the newly
            generated, unique doc_value.
        """
        # Does entry have existing linked number
        if self.number is not None:
            # Does linked number match type of the entry?
            if entry_type == self.number.entry_type.value:
                # If yes all good
                return
            else:
                # Release existing number and store this doc's pk in the comment field
                self._release_number()
        
        if confirmed_number:
            # Frontend confirmed a specific final value to create
            if entry_type == TypeEnum.drawing.value:
                num_obj = Number._make_number(confirmed_number, TypeEnum.drawing)
            else:
                # num_obj = Number._make_number(confirmed_number, TypeEnum.document)
                num_obj = None

            if num_obj:
                db.session.add(num_obj)
                self.number = num_obj
            return

        # If we're here, either didn't have a Number in the first place, or was released
        # Make new associated number change controlled drawings only
        number = Number._generate_number(change_controlled, entry_type, user_value)
        if number:
            db.session.add(number)
            self.number = number


    @classmethod
    def _generate_doc_identifier(cls):
        """
        Class method to generate a new, unique doc_identifier for a new document.
        The doc_identifier follows the pattern: 'stpyyymm_nnnn', where y=year,
        m=month, n=number.

        Returns
        -------
        str
            Generated doc_identifier.

        Raises
        ------
        e
            Exception raised if no document already exists with a doc identifier
            containing the current year & month.
        ValueError
            Exception raised if document already exists in the db with the newly
            generated, unique doc_identifier.
        ValueError
            Exception raised if document exists with a doc identifier containing
            the current year & month, but it doesn't follow the expected pattern
            ('stpyyymm_nnnn').
        """
        start_str = "stp"

        # Get db server time now (to be consistent with creation & update times).
        # Don't have access to the creation time (gets generated at db level), so
        # this is the next best thing.
        now = db.session.execute(func.now()).all()[0][0]

        # Build the datetime stub of the doc identifier
        doc_identifier_dt = f'{start_str}{now.strftime("%Y%m")}_'

        # Find the latest Document entry with this doc_identifier stub
        try:
            document = db.session.scalars(
                select(Document)
                .where(Document.doc_identifier.like(f"{doc_identifier_dt}%")) 
                .order_by(Document.time_created.desc())
                .limit(1)
            ).first()
        except Exception as e:
            logging.error(
                f"Documents: Generating doc_identifier for new doc. " f"Error: {e}"
            )
            raise e

        if document:
            # If document with given stub exists, get its numerical part
            pattern_match = re.match(
                rf"{start_str}\d{{6}}_(?P<number>\d{{4}})", document.doc_identifier
            )
            highest_number = pattern_match.groupdict().get("number")

            if highest_number:
                # Documents have already been added this month.
                # Build the next doc_identifier.
                incremented = int(highest_number) + 1
                doc_identifier = f"{doc_identifier_dt}{incremented:04d}"

                # Sanity check that it doesn't exist
                # found = db.session.scalars(
                #     select(exists().where(Document.doc_identifier==doc_identifier))
                # ).first()
                found = db.session.scalars(select(Document).where(Document.doc_identifier == doc_identifier).limit(1)).first()
                if found:
                    raise ValueError(
                        "Documents: Generating doc_identifier for new "
                        "doc. Document already exists with generated "
                        f"doc_identifier {doc_identifier}. HELP"
                    )
            else:
                # We're in uncharted waters, pattern should have found a match
                raise ValueError(
                    "Documents: Generating doc_identifier for new doc. "
                    "Document matching stub found, but no highest_number "
                    f"found. Match: {pattern_match.groupdict()}. HELP"
                )
        else:
            # No document found with given stub.
            # New month, no documents added yet.
            doc_identifier = f"{doc_identifier_dt}0001"

        return doc_identifier

    @classmethod
    def prepare_fields(cls, **kwargs):
        """
        To be used on new entry only!
        Class method to generate doc_identifier and check url fields before
        adding a new entry in the documents table.

        Returns
        -------
        dict
            dictionary of field names and values ready to create a new Document
            object
        """
        kwargs["doc_identifier"] = cls._generate_doc_identifier()

        if kwargs.get("compiled_url"):
            kwargs["compiled_url"] = cls._check_http(kwargs["compiled_url"])

        if kwargs.get("source_url"):
            kwargs["source_url"] = cls._check_http(kwargs["source_url"])

        return kwargs

    @classmethod
    def duplicate_exists(cls, field_name, **kwargs):
        """
        Class method to check if entry with the same given field exists before
        adding a new entry in the documents table.

        Parameters
        ----------
        field_name : str
            name of field for which to check if duplicate exists

        Returns
        -------
        bool
            true if existing entry found, false if no existing entry found

        Raises
        ------
        ValueError
            Exception raised if field isn't one of the keys of kwargs.
        """
        if kwargs.get(field_name):
            duplicate = db.session.scalars(
                select(Document).filter(getattr(Document, field_name)==kwargs[field_name]).limit(1)
            ).first()
            if duplicate:
                return True
            return False

        raise ValueError("Documents: Searching for duplicate on non-existing field.")

    @classmethod
    def create(cls, **kwargs):
        """
        Class method to create a new object and add a new entry in the
        documents table.

        Returns
        -------
        bool or Document object
            If table successfully updated and object succesfully created,
            object is returned, otherwise returns False.
        """
        try:
            kwargs = cls.prepare_fields(**kwargs)
            if cls.duplicate_exists("title", **kwargs):
                raise ValueError("Documents: An entry with this title already exists")

            number = kwargs.pop("number")
            confirmed_number = kwargs.pop("confirmed_number", None)
            obj = Document(**kwargs)

            # Make new associated number (for change controlled drawings and all docs)
            if confirmed_number:
                # Create exact number object when frontend confirmed suggested value
                if kwargs.get("entry_type") == TypeEnum.drawing.value:
                    num_obj = Number._make_number(confirmed_number, TypeEnum.drawing)
                else:
                    num_obj = Number._make_number(confirmed_number, TypeEnum.document)
                if num_obj:
                    db.session.add(num_obj)
                    obj.number = num_obj
            else:
                number = Number._generate_number(kwargs.get("change_controlled"), 
                                                kwargs.get("entry_type"), 
                                                number)
                if number:
                    db.session.add(number)
                    obj.number = number

            db.session.add(obj)
            db.session.commit()
            logger.info("Documents: Creating Document object.")
            return obj
        except (NumberConfirmationRequired, OutOfOrderNumber):
            # Let caller (views) handle confirmation / out-of-order flows
            raise
        except Exception as e:
            logger.error(f"Documents: Creating Document object. Error: {e}")
            return False

    @classmethod
    def get_by_doc_identifier(cls, doc_identifier, raise_not_found=False):
        """
        Class method that retrieves entry for a given doc_identifier and logs errors.


        Parameters
        ----------
        doc_identifier : str
            doc_identifier of entry to be found
        raise_not_found : bool
            False if we want to log and silence or True if we want to actually raise an 
            error if document with given doc_identifier is not found. Defaults to False.

        Returns
        -------
        Document object or None
            Document object with given doc_identifier is returned if query succesful,
            otherwise None is returned if no results found or more than one result
            found.
        """
        try:
            document = db.session.scalars(
                select(Document).filter_by(doc_identifier=doc_identifier)
            ).one()
            return document
        except NoResultFound as e:
            if raise_not_found:
                raise e
            else:
                logger.error(
                    f"Document: Error: {e}:\n Document with doc_identifier "
                    f"{doc_identifier} not found."
                )
                return None
        except MultipleResultsFound as e:
            logger.error(
                f"Document: Error: {e}:\n More than one document found "
                f"with doc_identifier {doc_identifier}"
            )
            return None

    @classmethod
    def get_by_doc_string(cls, doc_string):
        """
        Class method that searches entry for a given doc_string.
        The method tries to match the doc_string first with doc_identifiers,
        then, if a Number is associated with the object, with the Number value,
        and, finally, if any Aliases are associated with the object, with the
        Alias values.
        If at any point a match is found, the search is concluded and the match
        is returned.

        Parameters
        ----------
        doc_string : str
            doc_string to be matched

        Returns
        -------
        Document object or None
            Document object with given doc_identifier is returned if query succesful,
            otherwise None is returned if no results found or more than one result
            found.
        """
        try:
            document =  cls.get_by_doc_identifier(doc_string, raise_not_found=True)
        except NoResultFound:
            # Not an issue if not found, it's probably a number or an alias
            pass
        else:
            # Only happens if try was successful and we have a document variable
            if document is not None:
                return document

        number =  Number.get_by_value(doc_string)
        if number is not None:
            return number.document

        alias =  Alias.get_by_value(doc_string)
        if alias is not None:
            return alias.document

        return None


    def delete_doc(self):
        """
        Class method that deletes table entry.

        Returns
        -------
        bool
            If delete was successful, returns True, otherwise returns False
        """
        try:
            self._release_number()
            db.session.delete(self)
            db.session.commit()
            logger.info("Documents: Deleting Document object.")
            return True
        except Exception as e:
            logger.error(f"Documents: Deleting Document object. Error: {e}")
            return False

    def _release_number(self):
        if self.number is not None:
            number = self.number
            self.number = None
            number.comment = f"{number.comment};{self.pk}"
            db.session.add(self)
            db.session.add(number)
            logger.info("Document: Number found on Document object. Releasing Number.")
            db.session.commit()


class User(db.Model, Serializer):
    """
    User model class to act as interface between the Flask logic and the
    sql table.
    """

    pk = db.Column("pk", db.Integer, primary_key=True)
    email = db.Column("email", db.String(100), nullable=False, unique=True)
    superuser = db.Column("superuser", db.Boolean, default=False, nullable=False)
    access = db.Column("access", db.Integer, nullable=True)  # future-proofing

    @validates("email")
    def validate_email(self, key, email):
        if not email:
            raise AssertionError("No email provided")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise AssertionError("Provided email is not an email address")
        return email

    def update(self, **kwargs):
        """
        Method to update an existing object's column values with those in the
        kwargs.

        Returns
        -------
        bool
            Returns True is update was successful and False if an error was
            encountered.
        """
        try:
            for column in ["email", "superuser"]:
                new_val = kwargs.get(column, None)

                if column == "superuser":
                    if new_val == "":
                        new_val = False

                if new_val is not None:
                    setattr(self, column, new_val)
            db.session.add(self)
            db.session.commit()
            logger.info("Users: Updating User object.")
        except Exception as e:
            logger.error(f"Users: Updating User object. Error: {e}")
            return False
        return True

    @classmethod
    def create(cls, **kwargs):
        """
        Class method to create a new object and add a new entry in the
        user table.

        Returns
        -------
        bool or User object
            If table successfully updated and object succesfully created,
            object is returned, otherwise returns False.
        """
        try:
            data = {"email": kwargs["email"]}
            if kwargs["superuser"]:
                data["superuser"] = kwargs["superuser"]
            obj = User(**data)
            db.session.add(obj)
            db.session.commit()
            logger.info("Users: Creating User object.")
            return obj
        except Exception as e:
            logger.error(f"Users: Creating User object. Error: {e}")
            return False

    @classmethod
    def get_by_email(cls, email):
        """
        Class method that retrieves user for a given email and logs errors.


        Parameters
        ----------
        email : str
            email of user to be found

        Returns
        -------
        User object or None
            User object with given email is returned if query succesful,
            otherwise None is returned if no results found or more than one result
            found.
        """
        try:
            user = db.session.scalars(select(User).where(User.email==email)).one()
            return user
        except NoResultFound as e:
            logger.error(f"User: Error: {e}:\n User with email " f"{email} not found.")
            return None

    @classmethod
    def get_by_pk(cls, pk):
        """
        Class method that retrieves user for a given primary key and logs errors.

        Parameters
        ----------
        pk : int / str
            pk of user to be found

        Returns
        -------
        User object or None
            User object with given pk is returned if query succesful,
            otherwise None is returned if no results found.
        """
        try:
            user = db.session.scalars(select(User).where(User.pk==int(pk))).one()
            return user
        except NoResultFound as e:
            logger.error(f"User: Error: {e}:\n User with pk " f"{pk} not found.")
            return None

    def delete_user(self):
        """
        Class method that deletes table entry.

        Returns
        -------
        bool
            If delete was successful, returns True, otherwise returns False
        """
        try:
            db.session.delete(self)
            db.session.commit()
            logger.info("User: Deleting User object.")
            return True
        except Exception as e:
            logger.error(f"User: Deleting User object. Error: {e}")
            return False


class Domain(db.Model, Serializer):
    """
    Domain model class to act as interface between the Flask logic and the
    sql table.
    """

    pk = db.Column("pk", db.Integer, primary_key=True)
    email_domain = db.Column(
        "email_domain", db.String(100), nullable=False, unique=True
    )
    access = db.Column("access", db.Integer, nullable=True)  # future-proofing

    @validates("email_domain")
    def validate_email_domain(self, key, email_domain):
        if not email_domain:
            raise AssertionError("No email_domain provided")
        if not re.match(r"[^@]+\.[^@]+", email_domain):
            raise AssertionError("Provided email_domain is not valid")
        return email_domain

    def update(self, **kwargs):
        """
        Method to update an existing object's column values with those in the
        kwargs.

        Returns
        -------
        bool
            Returns True is update was successful and False if an error was
            encountered.
        """
        try:
            new_val = kwargs.get("email_domain", None)

            if new_val is not None:
                setattr(self, "email_domain", new_val)
            db.session.add(self)
            db.session.commit()
            logger.info("Domains: Updating Domain object.")
        except Exception as e:
            logger.error(f"Domains: Updating Domain object. Error: {e}")
            return False
        return True

    @classmethod
    def create(cls, **kwargs):
        """
        Class method to create a new object and add a new entry in the
        domain table.

        Returns
        -------
        bool or Domain object
            If table successfully updated and object succesfully created,
            object is returned, otherwise returns False.
        """
        try:
            data = {"email_domain": kwargs["email_domain"]}
            obj = Domain(**data)
            db.session.add(obj)
            db.session.commit()
            logger.info("Domains: Creating Domain object.")
            return obj
        except Exception as e:
            logger.error(f"Domains: Creating Domain object. Error: {e}")
            return False

    @classmethod
    def get_by_email_domain(cls, email_domain):
        """
        Class method that retrieves entry for a given email_domain and logs errors.

        Parameters
        ----------
        email_domain : str
            email_domain of entry to be found

        Returns
        -------
        Domain object or None
            Domain object with given email_domain is returned if query succesful,
            otherwise None is returned if no results found or more than one result
            found.
        """
        try:
            domain = db.session.scalars(
                select(Domain).where(Domain.email_domain==email_domain)
            ).one()
            return domain
        except NoResultFound as e:
            logger.error(
                f"User: Error: {e}:\n Domain with email_domain "
                f"{email_domain} not found."
            )
            return None

    @classmethod
    def get_by_email(cls, email):
        """
        Class method that retrieves entry for a given email and logs errors.

        Parameters
        ----------
        email : str
            email with email_domain of entry to be found

        Returns
        -------
        Domain object or None
            Domain object with given email_domain is returned if query succesful,
            otherwise None is returned if no results found or more than one result
            found.
        """
        email_domain = email.split("@")[1]
        return cls.get_by_email_domain(email_domain)

    @classmethod
    def get_by_pk(cls, pk):
        """
        Class method that retrieves domain for a given primary key and logs errors.

        Parameters
        ----------
        pk : int / str
            pk of domain to be found

        Returns
        -------
        Domain object or None
            Domain object with given pk is returned if query succesful,
            otherwise None is returned if no results found.
        """
        try:
            domain = db.session.scalars(select(Domain).where(Domain.pk==int(pk))).one()
            return domain
        except NoResultFound as e:
            logger.error(f"Domain: Error: {e}:\n Domain with pk " f"{pk} not found.")
            return None

    def delete_domain(self):
        """
        Class method that deletes table entry.

        Returns
        -------
        bool
            If delete was successful, returns True, otherwise returns False
        """
        try:
            db.session.delete(self)
            db.session.commit()
            logger.info("Domain: Deleting Domain object.")
            return True
        except Exception as e:
            logger.error(f"Domain: Deleting Domain object. Error: {e}")
            return False


class Number(db.Model, Serializer):
    """
    Number model class to act as interface between the Flask logic and the
    sql table.
    """

    pk = db.Column("pk", db.Integer, primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    value = db.Column("value", db.String(50), nullable=False)
    entry_type = db.Column("entry_type", db.Enum(TypeEnum), nullable=False)
    comment = db.Column("comment", db.String(200), default="")

    # Relationship to Document
    document_pk = db.Column("document_pk", db.Integer, db.ForeignKey('document.pk'))
    document = db.relationship("Document", back_populates="number")


    def __repr__(self):
        """
        Magic method that returns the string representation of the Number model.

        Returns
        -------
        str
            String representation of the Number model.
        """
        return "<Number %r>" % self.value

    def _get_all_columns(self):
        """
        Private method to return a list of all the model's columns.

        Returns
        -------
        list
            List of all the model's columns
        """
        return inspect(self).attrs.keys()

    @classmethod
    def get_by_value(cls, value):
        """
        Class method that retrieves entry for a given value and logs errors.

        Parameters
        ----------
        value : str
            value of entry to be found

        Returns
        -------
        Number object or None
            Number object with given value is returned if query succesful,
            otherwise None is returned if no results found or more than one result
            found.
        """
        try:
            number = db.session.scalars(
                select(Number).where(Number.value==value)
            ).one()
            return number
        except NoResultFound as e:
            logger.error(
                f"Number: Error: {e}:\n Number with value {value} not found."
            )
            return None
        except MultipleResultsFound as e:
            logger.error(
                f"Number: Error: {e}:\n More than one number found "
                f"with value {value}"
            )
            return None

    @classmethod
    def _generate_doc_value(cls):
        """
        Class method to generate a new, unique value for a new number linked
        to a Document of type "document".
        The doc_value follows the pattern: 'PRL-DOC-#####', where #=digit (0-9).

        Returns
        -------
        str
            Generated value.

        Raises
        ------
        ValueError
            Exception raised if Number already exists in the db with the newly
            generated, unique value.
        ValueError
            Exception raised if Number exists with starting stub, 
            but the rest doesn't follow the expected pattern.
        """
        # Build the string stub of the doc value
        doc_value_str = 'PRL-DOC-'

        # Find the latest Number entry with this value stub
        number = db.session.scalars(
            select(Number)
            .where(Number.value.like(f"{doc_value_str}%"))
            .order_by(Number.value.desc())
            .limit(1)
        ).first()

        if number:
            # If number with given stub exists, get its numerical part
            pattern_match = re.match(
                rf"{doc_value_str}(?P<code>\d{{5}})", number.value
            )
            highest_number = pattern_match.groupdict().get("code")

            if highest_number:
                # Build the next doc_identifier.
                incremented = int(highest_number) + 1
                doc_value = f"{doc_value_str}{incremented:05d}"

                # Sanity check that it doesn't exist
                # found = db.session.scalars(select(exists().where(Number.value == doc_value))).first()
                found = db.session.scalars(select(Number).where(Number.value == doc_value).limit(1)).first()
                if found:
                    raise ValueError(
                        "Number: Generating number value for new "
                        "doc entry. Number already exists with generated "
                        f"doc_value {doc_value}. HELP"
                    )
            else:
                # We're in uncharted waters, pattern should have found a match
                raise ValueError(
                    "Number: Generating number value for new doc entry. "
                    "Number matching stub found, but no highest_number "
                    f"found. Match: {pattern_match.groupdict()}. HELP"
                )
        else:
            # No number found with given stub. No doc numbers added yet.
            doc_value = f"{doc_value_str}00001"

        logger.info(f"Number: Generating new doc value {doc_value}.")
        return doc_value

    @classmethod
    def _generate_drawing_value(cls, user_value):
        """
        Class method to generate a new, unique value for a new number linked
        to a Document of type "drawing".
        The value starts from the string pattern provided by the user (following
        the drawing trees).

        Returns
        -------
        str
            Generated value.

        Raises
        ------
        ValueError
            Exception raised if Number already exists in the db with the newly
            generated, unique value.
        ValueError
            Exception raised if user provided stub string doesn't 
            follow the expected pattern.
        ValueError
            Exception raised if Number exists with the stub, 
            but the rest doesn't follow the expected pattern.
        """
        if not user_value:
            raise ValueError("Number: No drawing stub provided by user.")

        user_value = user_value.rstrip("-")

        # If the user provided a numberat the end of the stub (with or without a hyphen),
        # validate that it is exactly three digits. If it's not, raise an error.
        m_len = re.match(r'^(?P<stub>.*?)-?(?P<num>\d+)$', user_value)
        if m_len:
            num_str = m_len.group("num")
            if len(num_str) != 3:
                raise ValueError(
                    f"Number: Provided numeric suffix '{num_str}' must be exactly 3 digits (e.g. '001')."
                )

        # If the user provided a 3-digit number at the end of the stub (with or without a hyphen): 
        # either require confirmation (if entries with that exact 3-digit
        # prefix already exist), or warn about out-of-order numbers.
        m = re.match(r'^(?P<stub>.*?)-?(?P<num>\d{3})$', user_value)
        if m:
            stub = m.group("stub").rstrip("-")
            provided = int(m.group("num"))

            prefix = f"{stub}{provided:03d}"

            # Check whether entries with this exact 3-digit exist (any config)
            existing = db.session.scalars(
                select(Number)
                .where(Number.value.like(f"{prefix}-%"))
                .order_by(Number.value.desc())
            ).all()

            if existing:
                logger.info('Before search for existing')
                values = [entry.value for entry in existing]
                # db search is sorted in descending value order, so use the first (highest) entry
                first_val = values[0]
                prefix_match = re.match(rf"{re.escape(prefix)}-(\d{{2}})$", first_val)
                highest_config = int(prefix_match.group(1)) if prefix_match else 0
                suggested = f"{prefix}-{highest_config+1:02d}"

                # Ask user for confirmation to create entry with incremented config
                msg_lines = [f"The following entries exist for {prefix}:"]
                msg_lines.extend([f"- {v}" for v in values])
                msg_lines.append(f"Do you confirm creating {suggested}?")
                message = "\n".join(msg_lines)
                raise NumberConfirmationRequired(suggested, message)

            # No entries with this exact 3-digit number exist. Check sequence for this stub.
            last_for_stub = db.session.scalars(
                select(Number)
                .where(Number.value.like(f"{stub}%"))
                .order_by(Number.value.desc())
                .limit(1)
            ).first()

            if last_for_stub:
                stub_match = re.match(rf"{re.escape(stub)}(\d{{3}})-(\d{{2}})", last_for_stub.value)
                highest_number = int(stub_match.group(1)) if stub_match else None
                next_num = (highest_number + 1) if highest_number is not None else 1

                if provided != next_num:
                    suggested_next = f"{stub}{next_num:03d}-00"
                    # Signal that provided number is out of sequence and suggest next
                    raise OutOfOrderNumber(suggested_next,
                        f"Number: Provided number {provided:03d} is out-of-order. Suggest {suggested_next}.")

            else:
                # No prior entries for this stub. Only 001 is acceptable as the first number.
                if provided != 1:
                    suggested_next = f"{stub}001-00"
                    raise OutOfOrderNumber(suggested_next,
                        f"Number: Provided number {provided:03d} is out-of-order. Suggest {suggested_next}.")

            # Provided number equals next in sequence or there were no prior entries
            drawing_value = f"{prefix}-00"
            found = db.session.scalars(select(Number).where(Number.value == drawing_value).limit(1)).first()
            if found:
                raise ValueError(
                    "Number: Generating number value for new "
                    "drawing entry. Number already exists with generated "
                    f"drawing_value {drawing_value}. HELP"
                )

            logger.info(f"Number: Generating new drawing value {drawing_value}.")
            return drawing_value

        # No explicit 3-digit provided by user: original behaviour (auto-increment last ###)
        number = db.session.scalars(
            select(Number)
            .where(Number.value.like(f"{user_value}%"))
            .order_by(Number.value.desc())
            .limit(1)
        ).first()

        if number:
            # Match against pattern: {user_value}###-##
            pattern_match = re.match(rf"{re.escape(user_value)}(\d{{3}})-(\d{{2}})", number.value)
            highest_number = pattern_match.group(1) if pattern_match else None

            if highest_number:
                incremented = int(highest_number) + 1
            else:
                # We're in uncharted waters, pattern should have found a match
                raise ValueError(
                    "Number: Generating number value for new drawing entry. "
                    "Number matching stub found, but no highest_number "
                    f"found. Match: {pattern_match.groupdict()}. HELP"
                )
        else:
            incremented = 1

        drawing_value = f"{user_value}{incremented:03d}-00"

        found = db.session.scalars(select(Number).where(Number.value == drawing_value).limit(1)).first()
        if found:
            raise ValueError(
                "Number: Generating number value for new "
                "drawing entry. Number already exists with generated "
                f"drawing_value {drawing_value}. HELP"
            )

        logger.info(f"Number: Generating new drawing value {drawing_value}.")
        return drawing_value

    @classmethod
    def _generate_number(cls, change_controlled, entry_type, user_value):
        """
        Class method to generate a new, unique value for a new number linked
        to a Document and to make a Number object with it. 
        Only creates Number objects for change controlled drawings.

        Parameters
        ----------
        change_controlled :
            value of Document object's change_controlled field
        entry_type :
            value of Document object's entry_type field
        user_value :
            user provided value; can be empty string

        Returns
        -------
        None or Number object
            If criteria for creating Number object are met, object is created and 
            returned, otherwise returns None.

        Raises
        ------
        ValueError
            Exception raised if document already exists in the db with the newly
            generated, unique doc_value.
        """
        # if entry_type == TypeEnum.document.value:
        #     value = cls._generate_doc_value()
        #     return cls._make_number(value, TypeEnum.document)

        # elif entry_type == TypeEnum.drawing.value:
        if entry_type == TypeEnum.drawing.value:
            if change_controlled == ChangeControlledEnum.yes.value:
                if not user_value:
                    raise ValueError(
                        "Number: No number provided by user for change controlled "
                        "drawing."
                    )
                
                value = cls._generate_drawing_value(user_value)
                return cls._make_number(value, TypeEnum.drawing)

        logger.info("Number: Criteria for creating Number not met.")
        return None
        

    @classmethod
    def _make_number(cls, value, entry_type):
        """
        Class method to make a new object.
        Not calling it "create" since this method doesn't save the object
        to the db.

        Parameters
        ----------
        value :
            user provided value; can be empty string

        Returns
        -------
        bool or Number object
            If Number object succesfully created, object is returned, 
            otherwise returns False.
        """
        try:
            obj = Number(value=value, entry_type=entry_type)
            logger.info(f"Number: Creating Number object of type {entry_type.value} "
                        f"and value {value}.")
            return obj
        except Exception as e:
            logger.error(f"Number: Creating Number object. Error: {e}")
            return False


class Alias(db.Model, Serializer):
    """
    Alias model class to act as interface between the Flask logic and the
    sql table.
    """

    pk = db.Column("pk", db.Integer, primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    value = db.Column("value", db.String(50), nullable=False)

    # Relationship to Document
    document_pk = db.Column("document_pk", db.Integer, db.ForeignKey('document.pk'))
    document = db.relationship("Document", back_populates="aliases")

    @classmethod
    def get_by_value(cls, value):
        """
        Class method that retrieves entry for a given value and logs errors.

        Parameters
        ----------
        value : str
            value of entry to be found

        Returns
        -------
        Alias object or None
            Alias object with given value is returned if query succesful,
            otherwise None is returned if no results found or more than one result
            found.
        """
        try:
            alias = db.session.scalars(
                select(Alias).where(Alias.value==value)
            ).one()
            return alias
        except NoResultFound as e:
            logger.error(
                f"Alias: Error: {e}:\n Alias with value {value} not found."
            )
            return None
        except MultipleResultsFound as e:
            logger.error(
                f"Alias: Error: {e}:\n More than one Alias found "
                f"with value {value}"
            )
            return None


def get_entity(email):
    user = User.get_by_email(email)
    if not user:
        logger.error(f"get_entity: {email} not in the Users table\n")
        domain = Domain.get_by_email(email)
        if not domain:
            logger.error(f"get_entity: {email} not in the Domains table\n")
            return False
        else:
            logger.info(f"get_entity: Domain exists for {email}\n")
            return domain
    else:
        logger.info(f"get_entity: User exists for {email}\n")
        return user


def is_superuser(entity):
    if isinstance(entity, User):
        return entity.superuser
    if isinstance(entity, Domain):
        return False
