import re

from sqlalchemy.sql import func
from sqlalchemy.inspection import inspect
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import validates
from app import db

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logger")


class Serializer(object):
    """A mix-in to serialize SQLAlchemy models."""

    def serialize(self):
        """
        Serializes a single model object.

        Returns
        -------
        dict
            A dictionary with object's column names as keys and values as values
        """
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(obj_list):
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
        return [m.serialize() for m in obj_list]


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
    doc_code = db.Column("doc_code", db.String(30), default="")
    compiled_url = db.Column("compiled_url", db.String(500), default="")
    source_url = db.Column("source_url", db.String(500), default="")
    abstract = db.Column("abstract", db.Text, default="")
    creator_email = db.Column("creator_email", db.String(100), nullable=False)

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
            set(columns) - set(["time_created", "time_udpate", "doc_identifier"])
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
            db.session.add(self)
            db.session.commit()
            logger.info("Documents: Updating Document object.")
        except Exception as e:
            logger.error(f"Documents: Updating Document object. Error: {e}")
            return False
        return True

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
        # Get db server time now (to be consistent with creation & update times).
        # Don't have access to the creation time (gets generated at db level), so
        # this is the next best thing.
        now = db.session.execute(func.now()).all()[0][0]

        # Build the datetime stub of the doc identifier
        doc_identifier_dt = f'stp{now.strftime("%Y%m")}_'

        # Find the latest Document entry with this doc_identifier stub
        try:
            document = db.session.scalars(
                db.select(cls)
                .where(cls.doc_identifier.startswith(doc_identifier_dt))
                .order_by(cls.time_created.desc())
            ).first()
        except Exception as e:
            logging.error(
                f"Documents: Generating doc_identifier for new doc. " f"Error: {e}"
            )
            raise e

        if document:
            # If document with given stub exists, get its numerical part
            pattern_match = re.match(
                r"stp\d{6}_(?P<number>\d{4})", document.doc_identifier
            )
            highest_number = pattern_match.groupdict().get("number")

            if highest_number:
                # Documents have already been added this month.
                # Build the next doc_identifier.
                incremented = int(highest_number) + 1
                doc_identifier = f"{doc_identifier_dt}{incremented:04d}"

                # Sanity check that it doesn't exist
                exists = db.session.scalars(
                    db.select(cls).filter_by(doc_identifier=doc_identifier)
                ).first()
                if exists:
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
    def duplicate_exists(cls, **kwargs):
        """
        Class method to check if entry with the same title exists before
        adding a new entry in the documents table.

        Returns
        -------
        bool
            true if existing entry found, false if no existing entry found
        """
        duplicate = db.session.scalars(
            db.select(cls).filter_by(title=kwargs["title"])
        ).first()
        if duplicate:
            return True
        return False

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
            if cls.duplicate_exists(**kwargs):
                raise ValueError("Documents: An entry with this title already exists")

            obj = cls(**kwargs)
            db.session.add(obj)
            db.session.commit()
            logger.info("Documents: Creating Document object.")
            return obj
        except Exception as e:
            logger.error(f"Documents: Creating Document object. Error: {e}")
            return False

    @classmethod
    def get_by_doc_identifier(cls, doc_identifier):
        """
        Class method that retrieves entry for a given doc_identifier and logs errors.


        Parameters
        ----------
        doc_identifier : str
            doc_identifier of entry to be found

        Returns
        -------
        Document object or None
            Document object with given doc_identifier is returned if query succesful,
            otherwise None is returned if no results found or more than one result
            found.
        """
        try:
            document = db.session.scalars(
                db.select(cls).filter_by(doc_identifier=doc_identifier)
            ).one()
            return document
        except NoResultFound as e:
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

    def delete_doc(self):
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
            logger.info("Documents: Deleting Document object.")
            return True
        except Exception as e:
            logger.error(f"Documents: Deleting Document object. Error: {e}")
            return False


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
        if not re.match("[^@]+@[^@]+\.[^@]+", email):
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
            obj = cls(**data)
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
            user = db.session.scalars(db.select(cls).filter_by(email=email)).one()
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
            user = db.session.scalars(db.select(cls).filter_by(pk=int(pk))).one()
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
        if not re.match("[^@]+\.[^@]+", email_domain):
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
            obj = cls(**data)
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
                db.select(cls).filter_by(email_domain=email_domain)
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
            domain = db.session.scalars(db.select(cls).filter_by(pk=int(pk))).one()
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
