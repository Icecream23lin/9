from flask import Blueprint

config_bp = Blueprint('config', __name__)

@config_bp.route('/config/test', methods=['GET'])
def test_config():
    return {'message': 'Config blueprint is working!'}