from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import Transacao, Categoria, Usuario
from .forms import TransacaoForm, LoginForm, RegistroForm
from app import db
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash


main = Blueprint('main', __name__)

@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    
    transacoes = Transacao.query.filter_by(
        usuario_id=current_user.id
    ).order_by(Transacao.data.desc()).limit(5).all()
    
    receitas_total = sum(
        t.valor for t in Transacao.query.filter_by(
            tipo='receita',
            usuario_id=current_user.id
        ).all()
    )
    
    despesas_total = sum(
        t.valor for t in Transacao.query.filter_by(
            tipo='despesa',
            usuario_id=current_user.id
        ).all()
    )
    
    return render_template(
        'index.html',
        transacoes=transacoes,
        receitas_total=receitas_total,
        despesas_total=despesas_total
    )

@main.route('/transacoes', methods=['GET', 'POST'])
@login_required
def transacoes():
    form = TransacaoForm()
    query = Transacao.query.filter_by(usuario_id=current_user.id)
    
    if request.args.get('tipo'):
        query = query.filter_by(tipo=request.args['tipo'])
    
    transacoes = query.order_by(Transacao.data.desc()).all()

    if form.validate_on_submit():
        try:
            categoria = Categoria.query.filter_by(
                nome=form.categoria.data,
                usuario_id=current_user.id
            ).first()
            
            if not categoria:
                categoria = Categoria(
                    nome=form.categoria.data,
                    tipo=form.tipo.data,
                    usuario_id=current_user.id
                )
                db.session.add(categoria)
                db.session.flush()

            nova_transacao = Transacao(
                descricao=form.descricao.data,
                valor=form.valor.data,
                tipo=form.tipo.data,
                data=form.data.data,
                categoria_id=categoria.id,
                usuario_id=current_user.id
            )
            
            db.session.add(nova_transacao)
            db.session.commit()
            flash('Transação adicionada com sucesso!', 'success')
            return redirect(url_for('main.transacoes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar transação: {str(e)}', 'danger')

    return render_template('add_transacao.html', form=form, transacoes=transacoes)

@main.route('/transacoes/<int:id>/delete', methods=['POST'])
@login_required
def delete_transacao(id):
    transacao = Transacao.query.filter_by(
        id=id,
        usuario_id=current_user.id
    ).first_or_404()
    
    db.session.delete(transacao)
    db.session.commit()
    flash('Transação removida com sucesso!', 'success')
    return redirect(url_for('main.transacoes'))

@main.route('/transacoes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_transacao(id):
    transacao = Transacao.query.filter_by(
        id=id,
        usuario_id=current_user.id
    ).first_or_404()
    
    form = TransacaoForm(obj=transacao)
    
    if form.validate_on_submit():
        try:
            transacao.descricao = form.descricao.data
            transacao.valor = form.valor.data
            transacao.tipo = form.tipo.data
            transacao.data = form.data.data
            
            db.session.commit()
            flash('Transação atualizada com sucesso!', 'success')
            return redirect(url_for('main.transacoes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar transação: {str(e)}', 'danger')
    
    return render_template('editar_transacao.html', form=form, transacao=transacao)

@main.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        if not all([nome, email, senha]):
            flash('Preencha todos os campos!', 'danger')
            return redirect(url_for('main.registro'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'danger')
            return redirect(url_for('main.registro'))
        
        novo_usuario = Usuario(nome=nome, email=email)
        novo_usuario.set_password(senha)
        db.session.add(novo_usuario)
        db.session.commit()
        
        login_user(novo_usuario)
        flash('Usuário registrado com sucesso!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('registro.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        senha = form.senha.data
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_password(senha):
            login_user(usuario)
            return redirect(url_for('main.index'))
        else:
            flash('Email ou senha incorretos!', 'danger')
    
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('main.login'))


    