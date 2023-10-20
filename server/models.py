import re

from sqlalchemy.sql import func
from sqlalchemy.inspection import inspect
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from app import db

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('logger')

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
    sqlite table.
    """
    pk = db.Column('pk', db.Integer, primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    title = db.Column('title', db.String(500), nullable=False)
    author = db.Column('author', db.String(500), nullable=False)    
    doc_identifier = db.Column('doc_identifier', db.String(20), nullable=False)
    doc_code = db.Column('doc_code', db.String(10))
    compiled_url = db.Column('compiled_url', db.String(500))
    source_url = db.Column('source_url', db.String(500))
    abstract = db.Column('abstract', db.Text)
    creator_email = db.Column('creator_email', db.String(100), nullable=False)

    def __repr__(self):
        """
        Magic method that returns the string representation of the Document model.

        Returns
        -------
        str
            String representation of the Document model.
        """ 
        return '<Document %r>' % self.title
    
    def _get_editable_columns(self):
        """
        Private method to return a list of the model's editable columns.

        Returns
        -------
        list
            List of the model's editable columns
        """
        columns = inspect(self).attrs.keys()
        return list(set(columns) - 
                    set(['time_created', 'time_udpate', 'doc_identifier']))
    
    def _get_all_columns(self):
        """
        Private method to return a list of all the model's columns.

        Returns
        -------
        list
            List of all the model's columns
        """
        return inspect(self).attrs.keys()

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
                if new_val is not None:
                    setattr(self, column, new_val)
            db.session.add(self)
            db.session.commit()   
            logger.info('Documents: Updating Document object.')
        except Exception as e:
            logger.error(f'Documents: Updating Document object. Error: {e}')  
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
            document = db.session.scalars(db.select(cls).
                                      where(cls.doc_identifier.startswith(doc_identifier_dt)).
                                      order_by(cls.time_created.desc())
                                      ).first()
        except Exception as e:
            logging.error(f"Documents: Generating doc_identifier for new doc. "
                          f"Error: {e}")
            raise e

        if document:
            # If document with given stub exists, get its numerical part
            pattern_match = re.match(r'stp\d{6}_(?P<number>\d{4})', 
                                     document.doc_identifier)
            highest_number = pattern_match.groupdict().get('number')
        
            if highest_number:
                # Documents have already been added this month. 
                # Build the next doc_identifier.
                incremented = int(highest_number) + 1
                doc_identifier = f"{doc_identifier_dt}{incremented:04d}"

                # Sanity check that it doesn't exist
                exists = db.session.scalars(db.select(cls)
                                            .filter_by(doc_identifier=doc_identifier)).first()
                if exists:
                    raise ValueError("Documents: Generating doc_identifier for new "
                                    "doc. Document already exists with generated "
                                    f"doc_identifier {doc_identifier}. HELP")
            else:
                # We're in uncharted waters, pattern should have found a match
                raise ValueError("Documents: Generating doc_identifier for new doc. "
                                "Document matching stub found, but no highest_number "
                                f"found. Match: {pattern_match.groupdict()}. HELP")
        else:
            # No document found with given stub.
            # New month, no documents added yet.
            doc_identifier = f"{doc_identifier_dt}0001"

        return doc_identifier
    
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
            kwargs['doc_identifier'] = cls._generate_doc_identifier()
            obj = cls(**kwargs)
            db.session.add(obj)
            db.session.commit()
            logger.info('Documents: Updating Document object.')        
            return obj
        except Exception as e:
            logger.error(f'Documents: Creating Document object. Error: {e}')  
            return False

    @classmethod
    def get_by_doc_identifier(cls, doc_identifier):
        """
        Class method that retrieves entry for a given doc_identifier and logs errors.


        Parameters
        ----------
        doc_identifier : str
            doc_identifier of entry to be deleted

        Returns
        -------
        Document object or None
            Document object with given doc_identifier is returned if query succesful,
            otherwise None is returned if no results found or more than one result 
            found.
        """
        try:
            document = db.session.scalars(db.select(cls).
                                      filter_by(doc_identifier=doc_identifier)).one()
            return document
        except NoResultFound as e:
            logger.error(f'AllDocuments: Error: {e}:\n Document with doc_identifier '
                        f'{doc_identifier} not found.') 
            return None
        except MultipleResultsFound as e:
            logger.error(f'AllDocuments: Error: {e}:\n More than one document found '
                        f'with doc_identifier {doc_identifier}')
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
            logger.info('Documents: Deleting Document object.')   
            return True
        except Exception as e:
            logger.error(f'Documents: Deleting Document object. Error: {e}')  
            return False
