from flask import jsonify, request
from flask.views import MethodView

from models import db, Document

import logging

logger = logging.getLogger('logger')

# sanity check route
class Ping(MethodView):
    def get(self):
        logger.info('Pong!')
        return jsonify('pong!')

class AllDocuments(MethodView):
    """View class for the /documents route."""

    def post(self):
        """
        Method with logic for post requests.
        Post requests are made here when the user adds a new document.

        Returns
        -------
        json
            Json response to post request. Contains 'status' and 'message'.
        """
        response_object = {'status': 'success'}
        logger.info('AllDocuments: User is adding new document.')
        post_data = request.get_json()
        # TODO need to check if this isn't a duplicate
        # TODO should validate fields
        success = Document.create(**post_data)
        if not success:
            response_object['status'] = 'fail'            
        response_object['message'] = 'Document added!'
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
        logger.info('AllDocuments: User is viewing all documents.')
        documents = db.session.scalars(db.select(Document))
        response_object = {'status': 'success', 
                           'documents': Document.serialize_list(documents)}
        return jsonify(response_object)


class SingleDocument(MethodView):
    """View class for the /document/<document_id> route."""

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
        logger.info('AllDocuments: User is viewing all documents.')
        response_object = {'status': 'success'}
        document = Document.get_by_doc_identifier(doc_identifier)
        if document:
            response_object['document'] = document.serialize()
        else:
            response_object['message'] = ('No document found.')
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
        response_object = {'status': 'success'}
        logger.info('SingleDocument: User is updating document.')
        post_data = request.get_json()
        document = Document.get_by_doc_identifier(doc_identifier)
        if document:
            success = document.update(**post_data)
            if not success:
                response_object['status': 'fail']
            response_object['message'] = 'Document updated!'
        else:
            response_object['message'] = 'Document not found'
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
        response_object = {'status': 'success'}
        logger.info('SingleDocument: User is deleting document.')
        success = Document.delete_by_doc_identifier(doc_identifier)
        if not success:
            response_object['status': 'fail']        
        response_object['message'] = 'Document removed!'
        return jsonify(response_object)
