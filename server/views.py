from functools import wraps
import logging

from flask import jsonify, request
from flask.views import MethodView
import firebase_admin
from firebase_admin import auth

from models import db, Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('logger')

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            firebase_admin.get_app()
        except Exception as e:
            firebase_admin.initialize_app()
            # return {'status': 'fail', 'error': f'{e}'}, 400
        
        token = request.headers.get('Authorization')
        
        if token:
            logger.info(f'TokenRequired: Extracted token: {token}')
                
            try:
                # decoded_token = auth.verify_id_token(token, check_revoked=True)
                decoded_token = auth.verify_id_token(token)
            except Exception as e:
                logger.error(f'TokenRequired: Error in decoding user token:\nmessage: {e}\nToken: {token}')
                # return jsonify({'status': 'fail', 'message': 'Token invalid'})
                return {'status': 'fail', 'message': 'Resource not available'}, 401
            else:
                logger.info('TokenRequired: Token successfully decoded')
                setattr(request, "decoded_token", decoded_token)
                setattr(request, "email", decoded_token.get('email'))
                return f(*args, **kwargs)
        logger.error('TokenRequired: No token found with request.')
        # return jsonify({'status': 'fail', 'message': 'User not logged in'})
        return {'status': 'fail', 'message': 'Resource not available'}, 401
    return decorated_function

# sanity check route
class Ping(MethodView):
    def get(self):
        logger.info('Pong!')
        return jsonify('pong!')

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
        response_object = {'status': 'success'}
        logger.info(f'AllDocuments: User {email} is adding new document.')
        post_data = request.get_json()
        post_data['creator_email'] = email
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
        email = getattr(request, "email")
        logger.info(f'AllDocuments: User {email} is viewing all documents.')                    
        documents = db.session.scalars(db.select(Document))

        # from flask import request

        response_object = {'status': 'success', 
                           'documents': Document.serialize_list(documents),
                        #    'origin': [request.environ.get('REMOTE_ADDR'), request.environ.get('SERVER_NAME'), request.environ.get('HTTP_HOST'), request.environ.get('HTTP_ORIGIN'), request.environ.get('HTTP_REFERER')]
                        }
        return jsonify(response_object)


class SingleDocument(MethodView):
    """View class for the /document/<document_id> route."""

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
        email = getattr(request, "email")        
        logger.info(f'AllDocuments: User {email} is viewing all documents.')
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
        email = getattr(request, "email")        
        response_object = {'status': 'success'}

        post_data = request.get_json()
        document = Document.get_by_doc_identifier(doc_identifier)
        if document:
            if document.creator_email != email:
                response_object['status': 'fail']
                response_object['message'] = 'User not authorized to update this document'
                logger.info(f'SingleDocument: User {email} tried to update document they do not own.')
                return jsonify(response_object)

            logger.info(f'SingleDocument: User {email} is updating document.')
            success = document.update(**post_data)
            if not success:
                response_object['status': 'fail']
            response_object['message'] = 'Document updated!'
        else:
            logger.info(f'SingleDocument: User {email} tried to update inexistent document.')
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
        email = getattr(request, "email")          
        response_object = {'status': 'success'}

        document = Document.get_by_doc_identifier(doc_identifier)
        if document:
            if document.creator_email != email:
                response_object['status': 'fail']
                response_object['message'] = 'User not authorized to delete this document'
                logger.info(f'SingleDocument: User {email} tried to delete document they do not own.')
                return jsonify(response_object)
            
            logger.info('SingleDocument: User is deleting document.')
            success = document.delete_doc()
            if not success:
                response_object['status': 'fail']        
            response_object['message'] = 'Document removed!'
        else:
            logger.info(f'SingleDocument: User {email} tried to delete inexistent document.')
            response_object['message'] = 'Document not found'            
        return jsonify(response_object)
