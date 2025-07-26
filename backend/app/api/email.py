from flask import Blueprint

email_bp = Blueprint('email', __name__)

@email_bp.route('/email/test', methods=['GET'])
def test_email():
    return {'message': 'Email blueprint is working!'}