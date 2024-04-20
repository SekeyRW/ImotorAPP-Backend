import stripe
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from os.path import join, dirname, realpath
from flask_mail import Mail
from flask_socketio import SocketIO

db = SQLAlchemy()
socketio = SocketIO()
migrate = Migrate()
ma = Marshmallow()
jwt = JWTManager()
bcrypt = Bcrypt()
mail = Mail()

UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/uploaded_img/')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'SUPER DUPER SUPER DUPER SECRET'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/dbimotorapp'
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://imotor:Imotor%4037@localhost/dbimotorapp'
    app.config["JWT_SECRET_KEY"] = "SUPER DUPER SUPER DUPER SECRET"
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400  # 1 day
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Set the Stripe API key here
    stripe.api_key = 'sk_test_51OluYsDvpPWaX3mF8TsPQg5AEU2bP9DnBad4jpBeNcs62Oev6umbEOIRdKRRc39RWmHOCiKJkKuOTOFu7Ke1RtRp00Upg2naRe'

    app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024

    app.config['MAIL_SERVER'] = 'smtp.office365.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = 'info@imotor.app'
    app.config['MAIL_PASSWORD'] = 'info@imotor@2024'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_DEFAULT_SENDER'] = ('Imotor.App', 'info@imotor.app')

    app.config['FRONTEND_URL'] = 'https://imotor.app'

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")
    ma.init_app(app)
    CORS(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    from .views import views
    app.register_blueprint(views, url_prefix='/api')
    from .auth import auth
    app.register_blueprint(auth, url_prefix='/api/auth')

    with app.app_context():
        db.create_all()

    return app
