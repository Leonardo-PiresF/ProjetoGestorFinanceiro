from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, NumberRange, Length, EqualTo, Email

class TransacaoForm(FlaskForm):
    descricao = StringField('Descrição', validators=[DataRequired(), Length(max=100)])
    valor = DecimalField('Valor', validators=[DataRequired(), NumberRange(min=0)], places=2)
    tipo = SelectField('Tipo', choices=[('receita', 'Receita'), ('despesa', 'Despesa')], validators=[DataRequired()])
    data = DateField('Data', format='%Y-%m-%d', validators=[DataRequired()])
    categoria = StringField('Categoria', validators=[Length(max=50)])
    submit = SubmitField('Adicionar Transação')

class MeuFormulario(FlaskForm):
    campo = StringField('Campo')
    enviar = SubmitField('Enviar')

class loginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Entrar')

class RegistroForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=50)])
    email = EmailField('Email', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Registrar')

    def validate(self):
        if not super().validate():
            return False
        if self.senha.data != self.confirmar_senha.data:
            self.confirmar_senha.errors.append('As senhas não coincidem.')
            return False
        return True

    