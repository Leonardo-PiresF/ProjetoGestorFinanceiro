from datetime import datetime
from flask_login import UserMixin
from app import db  

class Transacao(db.Model):
    __tablename__ = 'transacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  
    data = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    categoria = db.relationship('Categoria', back_populates='transacoes')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario = db.relationship('Usuario', back_populates='transacoes')

    def __init__(self, descricao, valor, tipo, data=None, categoria_id=None, usuario_id=None):
        self.descricao = descricao
        self.valor = valor
        self.tipo = tipo
        self.data = data or datetime.utcnow().date()  
        self.categoria_id = categoria_id
        self.usuario_id = usuario_id
    
    def __repr__(self):
        return f'<Transacao {self.descricao} - R${self.valor}>'

class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario', back_populates='categorias')
    transacoes = db.relationship('Transacao', back_populates='categoria')
    
    def __repr__(self):
        return f'<Categoria {self.nome}>'

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    transacoes = db.relationship('Transacao', back_populates='usuario')
    categorias = db.relationship('Categoria', back_populates='usuario')

    def __init__(self, nome, email, senha):
        self.nome = nome
        self.email = email
        self.set_password(senha)  

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.senha = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.senha, password)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<Usuario {self.nome}>'