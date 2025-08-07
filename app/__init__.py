from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os


db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder='../templates')
    
    
    app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
       
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    from .models import Usuario
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    from .routes import main
    app.register_blueprint(main)
       
    @app.route('/sua-rota')
    def sua_view():
        from .forms import MeuFormulario  
        from flask import render_template
        form = MeuFormulario()
        return render_template('seu_template.html', form=form)
    
    
    with app.app_context():
        db.create_all()
    
    return app