import re
import enum

from sqlalchemy import select, exists
from sqlalchemy.sql import func
from sqlalchemy.inspection import inspect
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import validates
from app import db

from models import Serializer, TypeEnum, ChangeControlledEnum, ChangeControlledType

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logger")


def _combine_and_pad(num1, num2, total_length):
    # Convert the numbers to strings
    num1_str = str(num1)
    num2_str = str(num2)
    
    # Calculate the required padding in the middle
    combined = num1_str + num2_str
    padding_needed = total_length - len(combined)
    
    if padding_needed > 0:
        # Pad with zeros in the middle
        return num1_str + '0' * padding_needed + num2_str
    else:
        # Log as error, but don't break
        if padding_needed < 0:
            logger.error("Numbers {num1} and {num2} combine to more "
                        "than {total_length} characters.")

        # If no padding is needed, just return the combined string
        return combined

class DemoDocument(db.Model, Serializer):
    """
    DemoDocument model class to act as interface between the Flask logic and the
    sql table.
    """
    __bind_key__ = "sqlite_db"
    __tablename__ = "document"

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

    # Relationship to DemoNumber
    number = db.relationship("DemoNumber", back_populates="document", uselist=False)

    # Relationship to DemoAlias
    aliases = db.relationship("DemoAlias", back_populates="document")


    def __repr__(self):
        """
        Magic method that returns the string representation of the DemoDocument model.

        Returns
        -------
        str
            String representation of the DemoDocument model.
        """
        return "<DemoDocument %r>" % self.title

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
                                kwargs.get("number"))
            db.session.add(self)
            db.session.commit()
            logger.info("DemoDocuments: Updating DemoDocument object.")
        except Exception as e:
            logger.error(f"DemoDocuments: Updating DemoDocument object. Error: {e}")
            return False
        return True

    def _update_number(self, change_controlled, entry_type, user_value):
        """
        Class method to check if entry to be updated already has a linked
        DemoNumber (in which case, validate that it matches the criteria) or not
        (in which case, trigger generation method).

        Parameters
        ----------
        change_controlled :
            value of DemoDocument object's change_controlled field
        entry_type :
            value of DemoDocument object's entry_type field
        user_value :
            user provided value; can be empty string

        Returns
        -------
        Bool or DemoNumber object
            If criteria for creating DemoNumber object are met, object is created and 
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
        
        # If we're here, either didn't have a Number in the first place, or was released
        # Make new associated number (for change controlled drawings and all docs)
        number = DemoNumber._generate_number(change_controlled, entry_type, user_value)
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

        # Find the latest DemoDocument entry with this doc_identifier stub
        try:
            document = db.session.scalars(
                select(DemoDocument)
                .where(DemoDocument.doc_identifier.like(f"{doc_identifier_dt}%")) 
                .order_by(DemoDocument.time_created.desc())
                .limit(1)
            ).first()
        except Exception as e:
            logging.error(
                f"DemoDocuments: Generating doc_identifier for new doc. " f"Error: {e}"
            )
            raise e

        if document:
            # If document with given stub exists, get its numerical part
            pattern_match = re.match(
                rf"{start_str}\d{{6}}_(?P<number>\d{{4}})", document.doc_identifier
            )
            highest_number = pattern_match.groupdict().get("number")

            if highest_number:
                # DemoDocuments have already been added this month.
                # Build the next doc_identifier.
                incremented = int(highest_number) + 1
                doc_identifier = f"{doc_identifier_dt}{incremented:04d}"

                # Sanity check that it doesn't exist
                # found = db.session.scalars(
                #     select(exists().where(DemoDocument.doc_identifier==doc_identifier))
                # ).first()
                found = db.session.scalars(select(DemoDocument).where(DemoDocument.doc_identifier == doc_identifier).limit(1)).first()
                if found:
                    raise ValueError(
                        "DemoDocuments: Generating doc_identifier for new "
                        "doc. DemoDocument already exists with generated "
                        f"doc_identifier {doc_identifier}. HELP"
                    )
            else:
                # We're in uncharted waters, pattern should have found a match
                raise ValueError(
                    "DemoDocuments: Generating doc_identifier for new doc. "
                    "DemoDocument matching stub found, but no highest_number "
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
            dictionary of field names and values ready to create a new DemoDocument
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
                select(DemoDocument).filter(getattr(DemoDocument, field_name)==kwargs[field_name]).limit(1)
            ).first()
            if duplicate:
                return True
            return False

        raise ValueError("DemoDocuments: Searching for duplicate on non-existing field.")

    @classmethod
    def create(cls, **kwargs):
        """
        Class method to create a new object and add a new entry in the
        documents table.

        Returns
        -------
        bool or DemoDocument object
            If table successfully updated and object succesfully created,
            object is returned, otherwise returns False.
        """
        try:
            kwargs = cls.prepare_fields(**kwargs)
            if cls.duplicate_exists("title", **kwargs):
                raise ValueError("DemoDocuments: An entry with this title already exists")

            number = kwargs.pop("number")
            obj = DemoDocument(**kwargs)

            # Make new associated number (for change controlled drawings and all docs)
            number = DemoNumber._generate_number(kwargs.get("change_controlled"), 
                                            kwargs.get("entry_type"), 
                                            number)
            if number:
                db.session.add(number)
                obj.number = number

            db.session.add(obj)
            db.session.commit()
            logger.info("DemoDocuments: Creating DemoDocument object.")
            return obj
        except Exception as e:
            logger.error(f"DemoDocuments: Creating DemoDocument object. Error: {e}")
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
        DemoDocument object or None
            DemoDocument object with given doc_identifier is returned if query succesful,
            otherwise None is returned if no results found or more than one result
            found.
        """
        try:
            document = db.session.scalars(
                select(DemoDocument).filter_by(doc_identifier=doc_identifier)
            ).one()
            return document
        except NoResultFound as e:
            if raise_not_found:
                raise e
            else:
                logger.error(
                    f"DemoDocument: Error: {e}:\n DemoDocument with doc_identifier "
                    f"{doc_identifier} not found."
                )
                return None
        except MultipleResultsFound as e:
            logger.error(
                f"DemoDocument: Error: {e}:\n More than one document found "
                f"with doc_identifier {doc_identifier}"
            )
            return None

    @classmethod
    def get_by_doc_string(cls, doc_string):
        """
        Class method that searches entry for a given doc_string.
        The method tries to match the doc_string first with doc_identifiers,
        then, if a DemoNumber is associated with the object, with the DemoNumber value,
        and, finally, if any DemoAliases are associated with the object, with the
        DemoAlias values.
        If at any point a match is found, the search is concluded and the match
        is returned.

        Parameters
        ----------
        doc_string : str
            doc_string to be matched

        Returns
        -------
        DemoDocument object or None
            DemoDocument object with given doc_identifier is returned if query succesful,
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

        number =  DemoNumber.get_by_value(doc_string)
        if number is not None:
            return number.document

        alias =  DemoAlias.get_by_value(doc_string)
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
            logger.info("DemoDocuments: Deleting DemoDocument object.")
            return True
        except Exception as e:
            logger.error(f"DemoDocuments: Deleting DemoDocument object. Error: {e}")
            return False

    def _release_number(self):
        if self.number is not None:
            number = self.number
            self.number = None
            number.comment = f"{number.comment};{self.pk}"
            db.session.add(self)
            db.session.add(number)
            logger.info("DemoDocument: DemoNumber found on DemoDocument object. Releasing DemoNumber.")
            db.session.commit()


class DemoUser(db.Model, Serializer):
    """
    User model class to act as interface between the Flask logic and the
    sql table.
    """
    __bind_key__ = "sqlite_db"
    __tablename__ = "user"

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
            obj = DemoUser(**data)
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
            user = db.session.scalars(select(DemoUser).where(DemoUser.email==email)).one()
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
            user = db.session.scalars(select(DemoUser).where(DemoUser.pk==int(pk))).one()
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


class DemoDomain(db.Model, Serializer):
    """
    Domain model class to act as interface between the Flask logic and the
    sql table.
    """
    __bind_key__ = "sqlite_db"
    __tablename__ = "domain"

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
            obj = DemoDomain(**data)
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
                select(DemoDomain).where(DemoDomain.email_domain==email_domain)
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
            domain = db.session.scalars(select(DemoDomain).where(DemoDomain.pk==int(pk))).one()
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


class DemoNumber(db.Model, Serializer):
    """
    DemoNumber model class to act as interface between the Flask logic and the
    sql table.
    """
    __bind_key__ = "sqlite_db"
    __tablename__ = "number"

    pk = db.Column("pk", db.Integer, primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    value = db.Column("value", db.String(50), nullable=False)
    entry_type = db.Column("entry_type", db.Enum(TypeEnum), nullable=False)
    comment = db.Column("comment", db.String(200), default="")

    # Relationship to DemoDocument
    document_pk = db.Column("document_pk", db.Integer, db.ForeignKey('document.pk'))
    document = db.relationship("DemoDocument", back_populates="number")


    def __repr__(self):
        """
        Magic method that returns the string representation of the DemoNumber model.

        Returns
        -------
        str
            String representation of the DemoNumber model.
        """
        return "<DemoNumber %r>" % self.value

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
        DemoNumber object or None
            DemoNumber object with given value is returned if query succesful,
            otherwise None is returned if no results found or more than one result
            found.
        """
        try:
            number = db.session.scalars(
                select(DemoNumber).where(DemoNumber.value==value)
            ).one()
            return number
        except NoResultFound as e:
            logger.error(
                f"DemoNumber: Error: {e}:\n DemoNumber with value {value} not found."
            )
            return None
        except MultipleResultsFound as e:
            logger.error(
                f"DemoNumber: Error: {e}:\n More than one number found "
                f"with value {value}"
            )
            return None

    @classmethod
    def _generate_doc_value(cls):
        """
        Class method to generate a new, unique value for a new number linked
        to a DemoDocument of type "document".
        The doc_value follows the pattern: 'PRL-DOC-#####', where #=digit (0-9).

        Returns
        -------
        str
            Generated value.

        Raises
        ------
        ValueError
            Exception raised if DemoNumber already exists in the db with the newly
            generated, unique value.
        ValueError
            Exception raised if DemoNumber exists with starting stub, 
            but the rest doesn't follow the expected pattern.
        """
        # Build the string stub of the doc value
        doc_value_str = 'PRL-DOC-'

        # Find the latest DemoNumber entry with this value stub
        number = db.session.scalars(
            select(DemoNumber)
            .where(DemoNumber.value.like(f"{doc_value_str}%"))
            .order_by(DemoNumber.value.desc())
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
                # found = db.session.scalars(select(exists().where(DemoNumber.value == doc_value))).first()
                found = db.session.scalars(select(DemoNumber).where(DemoNumber.value == doc_value).limit(1)).first()
                if found:
                    raise ValueError(
                        "DemoNumber: Generating number value for new "
                        "doc entry. DemoNumber already exists with generated "
                        f"doc_value {doc_value}. HELP"
                    )
            else:
                # We're in uncharted waters, pattern should have found a match
                raise ValueError(
                    "DemoNumber: Generating number value for new doc entry. "
                    "DemoNumber matching stub found, but no highest_number "
                    f"found. Match: {pattern_match.groupdict()}. HELP"
                )
        else:
            # No number found with given stub. No doc numbers added yet.
            doc_value = f"{doc_value_str}00001"

        logger.info(f"DemoNumber: Generating new doc value {doc_value}.")
        return doc_value

    @classmethod
    def _generate_drawing_value(cls, user_value):
        """
        Class method to generate a new, unique value for a new number linked
        to a DemoDocument of type "drawing".
        The value starts from the string pattern provided by the user (following
        the drawing trees).

        Returns
        -------
        str
            Generated value.

        Raises
        ------
        ValueError
            Exception raised if DemoNumber already exists in the db with the newly
            generated, unique value.
        ValueError
            Exception raised if user provided stub string doesn't 
            follow the expected pattern.
        ValueError
            Exception raised if DemoNumber exists with the stub, 
            but the rest doesn't follow the expected pattern.
        """
        counter_len = 4
        user_value = user_value.rstrip("-")

        # Find the latest DemoNumber entry with the user provided value stub
        number = db.session.scalars(
            select(DemoNumber)
            .where(DemoNumber.value.like(f"{user_value}%"))
            .order_by(DemoNumber.value.desc())
            .limit(1)
        ).first()

        if number:
            # If number with given stub exists, get its numerical part
            pattern_match = re.match(
                rf"{user_value}(?P<code>\d{{2,4}})", number.value
            )
            highest_number = pattern_match.groupdict().get("code")

            if highest_number:
                # Build the next doc_identifier.
                incremented = int(highest_number) + 1
            else:
                # We're in uncharted waters, pattern should have found a match
                raise ValueError(
                    "DemoNumber: Generating number value for new drawing entry. "
                    "DemoNumber matching stub found, but no highest_number "
                    f"found. Match: {pattern_match.groupdict()}. HELP"
                )
        else:
            # No number found with given stub. No doc numbers added yet.
            incremented = 1

        # Attach incremented integer to user-provided stub
        # This is more complicated, since user-provided stub can be of
        # several formats: 
        # ABC-DEF-#### or ABC-DEF-10## or ABC-DEF-A####
        components = user_value.split("-")
        if len(components[-1]) < 3:
            # Is the last component is a modifier or sufix, 
            # remove it and process it separately
            ending = components.pop()
            drawing_value_str = "-".join(components)

            # Is ending an integer?
            if ending.isdigit():
                counter = _combine_and_pad(ending, incremented, counter_len)
                drawing_value = f"{drawing_value_str}-{counter}"
            elif ending.isalpha():
                counter = str(incremented).zfill(4)
                drawing_value = f"{drawing_value_str}-{ending}{counter}"
            else:
                raise ValueError(
                    "DemoNumber: Generating number value for new "
                    f"drawing entry. User provided stub {user_value} doesn't "
                    "match expected format. HELP"
                )
        else:
            # No special processing needed, just take the user value and add
            # the incremented number
            drawing_value = f"{user_value}-{incremented:04d}"

        # Sanity check that it doesn't exist
        # found = db.session.scalars(select(exists().where(DemoNumber.value == drawing_value))).first()
        found = db.session.scalars(select(DemoNumber).where(DemoNumber.value == drawing_value).limit(1)).first()
        if found:
            raise ValueError(
                "DemoNumber: Generating number value for new "
                "drawing entry. DemoNumber already exists with generated "
                f"drawing_value {drawing_value}. HELP"
            )

        logger.info(f"DemoNumber: Generating new drawing value {drawing_value}.")
        return drawing_value

    @classmethod
    def _generate_number(cls, change_controlled, entry_type, user_value):
        """
        Class method to generate a new, unique value for a new number linked
        to a DemoDocument and to make a DemoNumber object with it. 

        Parameters
        ----------
        change_controlled :
            value of DemoDocument object's change_controlled field
        entry_type :
            value of DemoDocument object's entry_type field
        user_value :
            user provided value; can be empty string

        Returns
        -------
        None or DemoNumber object
            If criteria for creating DemoNumber object are met, object is created and 
            returned, otherwise returns None.

        Raises
        ------
        ValueError
            Exception raised if document already exists in the db with the newly
            generated, unique doc_value.
        """
        if entry_type == TypeEnum.document.value:
            value = cls._generate_doc_value()
            return cls._make_number(value, TypeEnum.document)

        elif entry_type == TypeEnum.drawing.value:
            if change_controlled == ChangeControlledEnum.yes.value:
                if not user_value:
                    raise ValueError(
                        "DemoNumber: No number provided by user for change controlled "
                        "drawing."
                    )
                
                value = cls._generate_drawing_value(user_value)
                return cls._make_number(value, TypeEnum.drawing)

        logger.info("DemoNumber: Criteria for creating DemoNumber not met.")
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
        bool or DemoNumber object
            If DemoNumber object succesfully created, object is returned, 
            otherwise returns False.
        """
        try:
            obj = DemoNumber(value=value, entry_type=entry_type)
            logger.info(f"DemoNumber: Creating DemoNumber object of type {entry_type.value} "
                        f"and value {value}.")
            return obj
        except Exception as e:
            logger.error(f"DemoNumber: Creating DemoNumber object. Error: {e}")
            return False


class DemoAlias(db.Model, Serializer):
    """
    DemoAlias model class to act as interface between the Flask logic and the
    sql table.
    """
    __bind_key__ = "sqlite_db"
    __tablename__ = "alias"

    pk = db.Column("pk", db.Integer, primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    value = db.Column("value", db.String(50), nullable=False)

    # Relationship to DemoDocument
    document_pk = db.Column("document_pk", db.Integer, db.ForeignKey('document.pk'))
    document = db.relationship("DemoDocument", back_populates="aliases")

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
        DemoAlias object or None
            DemoAlias object with given value is returned if query succesful,
            otherwise None is returned if no results found or more than one result
            found.
        """
        try:
            alias = db.session.scalars(
                select(DemoAlias).where(DemoAlias.value==value)
            ).one()
            return alias
        except NoResultFound as e:
            logger.error(
                f"DemoAlias: Error: {e}:\n DemoAlias with value {value} not found."
            )
            return None
        except MultipleResultsFound as e:
            logger.error(
                f"DemoAlias: Error: {e}:\n More than one DemoAlias found "
                f"with value {value}"
            )
            return None