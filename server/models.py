from sqlalchemy.inspection import inspect
from app import db

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
    title = db.Column('title', db.String(100), nullable=False)
    author = db.Column('author', db.String(100), nullable=False)    
    doc_identifier = db.Column('doc_identifier', db.String(20), nullable=False)
    doc_code = db.Column('doc_code', db.String(20))
    compiled_url = db.Column('compiled_url', db.String(100), unique=False)
    source_url = db.Column('source_url', db.String(100), unique=False)
    abstract = db.Column('abstract', db.Text)

    def __repr__(self):
        """
        Magic method that returns the string representation of the Document model.

        Returns
        -------
        str
            String representation of the Document model.
        """ 
        return '<Document %r>' % self.title
    
    def _get_columns(self):
        """
        Private method to return a list of the model's columns.

        Returns
        -------
        list
            List of the model's columns
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
        columns = self._get_columns()
        try:        
            for column in columns:
                new_val = kwargs.get(column, None)
                if new_val is not None:
                    setattr(self, column, new_val)
            db.session.add(self)
            db.session.commit()                    
        except Exception:
            return False
        return True
    
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
            obj = cls(**kwargs)
            db.session.add(obj)
            db.session.commit()
            return obj
        except Exception:
            return False

    @classmethod
    def delete_by_pk(cls, document_id):
        """
        Class method that deletes table entry with given primary key / id.

        Parameters
        ----------
        document_id : str / int
            Id / pk of entry to be deleted

        Returns
        -------
        bool
            If delete was successful, returns True, otherwise returns False
        """
        doc = cls.query.get(document_id)
        if doc:
            try:
                db.session.delete(doc)
                db.session.commit()
                return True
            except Exception:
                return False
        return False