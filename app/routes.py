from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import Transacao, Categoria, Usuario
from .forms import TransacaoForm, RegistroForm 
from app import db
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from collections import defaultdict
import json
from flask import make_response
import csv
from io import StringIO

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
    
    # Buscar transações do usuário atual
    query = Transacao.query.filter_by(usuario_id=current_user.id)
    
    # Filtro por tipo se especificado
    if request.args.get('tipo'):
        query = query.filter_by(tipo=request.args['tipo'])
    
    transacoes = query.order_by(Transacao.data.desc()).all()

    if form.validate_on_submit():
        try:
            # Buscar ou criar categoria
            categoria = None
            if form.categoria.data:  
                categoria = Categoria.query.filter_by(
                    nome=form.categoria.data.strip(),
                    tipo=form.tipo.data,
                    usuario_id=current_user.id
                ).first()
                
                if not categoria:
                    categoria = Categoria(
                        nome=form.categoria.data.strip(),
                        tipo=form.tipo.data,
                        usuario_id=current_user.id
                    )
                    db.session.add(categoria)
                    db.session.flush()  # Para obter o ID

            # Criar nova transação
            nova_transacao = Transacao(
                descricao=form.descricao.data.strip(),
                valor=float(form.valor.data),
                tipo=form.tipo.data,
                data=form.data.data,
                categoria_id=categoria.id if categoria else None,
                usuario_id=current_user.id
            )
            
            db.session.add(nova_transacao)
            db.session.commit()
            
            flash('Transação adicionada com sucesso!', 'success')
            return redirect(url_for('main.transacoes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar transação: {str(e)}', 'danger')
            print(f"Erro detalhado: {e}")  # Para debug

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
    
    return render_template('edit_transacao.html', form=form, transacao=transacao)

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
        
        novo_usuario = Usuario(nome=nome, email=email, senha=senha)
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
    
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_password(senha):
            login_user(usuario)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Email ou senha incorretos!', 'danger')
    
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('main.login'))


@main.route('/configuracoes')
@login_required
def configuracoes():
    return render_template('configuracoes.html')

@main.route('/relatorios')
@login_required
def relatorios():
    
    periodo = request.args.get('periodo', '30')  
    
    
    if periodo == '7':
        data_inicio = datetime.now().date() - timedelta(days=7)
    elif periodo == '30':
        data_inicio = datetime.now().date() - timedelta(days=30)
    elif periodo == '90':
        data_inicio = datetime.now().date() - timedelta(days=90)
    elif periodo == '365':
        data_inicio = datetime.now().date() - timedelta(days=365)
    else:
        data_inicio = datetime.now().date() - timedelta(days=30)
    
    
    transacoes = Transacao.query.filter(
        Transacao.usuario_id == current_user.id,
        Transacao.data >= data_inicio
    ).all()
    
    
    receitas_total = sum(t.valor for t in transacoes if t.tipo == 'receita')
    despesas_total = sum(t.valor for t in transacoes if t.tipo == 'despesa')
    saldo = receitas_total - despesas_total
    
    
    pizza_data = {
        'labels': ['Receitas', 'Despesas'],
        'values': [float(receitas_total), float(despesas_total)],
        'colors': ['#28a745', '#dc3545']
    }
    
    
    evolucao_diaria = defaultdict(lambda: {'receitas': 0, 'despesas': 0})
    
    for transacao in transacoes:
        data_str = transacao.data.strftime('%Y-%m-%d')
        if transacao.tipo == 'receita':
            evolucao_diaria[data_str]['receitas'] += float(transacao.valor)
        else:
            evolucao_diaria[data_str]['despesas'] += float(transacao.valor)
    
    
    datas_ordenadas = sorted(evolucao_diaria.keys())
    linha_data = {
        'labels': [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in datas_ordenadas],
        'receitas': [evolucao_diaria[d]['receitas'] for d in datas_ordenadas],
        'despesas': [evolucao_diaria[d]['despesas'] for d in datas_ordenadas]
    }
    
   
    categorias_receitas = defaultdict(float)
    categorias_despesas = defaultdict(float)
    
    for transacao in transacoes:
        categoria_nome = transacao.categoria.nome if transacao.categoria else 'Sem categoria'
        if transacao.tipo == 'receita':
            categorias_receitas[categoria_nome] += float(transacao.valor)
        else:
            categorias_despesas[categoria_nome] += float(transacao.valor)
    
    
    cat_receitas_data = {
        'labels': list(categorias_receitas.keys()),
        'values': list(categorias_receitas.values())
    }
    
    cat_despesas_data = {
        'labels': list(categorias_despesas.keys()),
        'values': list(categorias_despesas.values())
    }
    
    
    estatisticas = {
        'total_transacoes': len(transacoes),
        'media_receitas': float(receitas_total / max(len([t for t in transacoes if t.tipo == 'receita']), 1)),
        'media_despesas': float(despesas_total / max(len([t for t in transacoes if t.tipo == 'despesa']), 1)),
        'maior_receita': max([float(t.valor) for t in transacoes if t.tipo == 'receita'], default=0),
        'maior_despesa': max([float(t.valor) for t in transacoes if t.tipo == 'despesa'], default=0),
    }
    
    return render_template(
        'relatorios.html',
        receitas_total=receitas_total,
        despesas_total=despesas_total,
        saldo=saldo,
        periodo=periodo,
        pizza_data=json.dumps(pizza_data),
        linha_data=json.dumps(linha_data),
        cat_receitas_data=json.dumps(cat_receitas_data),
        cat_despesas_data=json.dumps(cat_despesas_data),
        estatisticas=estatisticas,
        transacoes=transacoes[:10]  
    )
@main.route('/exportar-csv')
@login_required
def exportar_csv():
    periodo = request.args.get('periodo', '30')
    
    # Calcular data inicial
    if periodo == '7':
        data_inicio = datetime.now().date() - timedelta(days=7)
    elif periodo == '30':
        data_inicio = datetime.now().date() - timedelta(days=30)
    elif periodo == '90':
        data_inicio = datetime.now().date() - timedelta(days=90)
    elif periodo == '365':
        data_inicio = datetime.now().date() - timedelta(days=365)
    else:
        data_inicio = datetime.now().date() - timedelta(days=30)
    
    # Buscar transações
    transacoes = Transacao.query.filter(
        Transacao.usuario_id == current_user.id,
        Transacao.data >= data_inicio
    ).order_by(Transacao.data.desc()).all()
    
    # Criar CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Cabeçalho
    writer.writerow(['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
    
    # Dados
    for transacao in transacoes:
        writer.writerow([
            transacao.data.strftime('%d/%m/%Y'),
            transacao.descricao,
            f'{transacao.valor:.2f}',
            transacao.tipo.title(),
            transacao.categoria.nome if transacao.categoria else 'Sem categoria'
        ])
    
    # Preparar resposta
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=relatorio_financeiro_{periodo}dias.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response