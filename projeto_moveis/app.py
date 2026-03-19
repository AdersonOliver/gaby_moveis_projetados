import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, Movel, Usuario  # Certifique-se de que a classe Usuario está no models.py
from werkzeug.utils import secure_filename

app = Flask(__name__)

# CONFIGURAÇÕES DE SEGURANÇA
app.config['SECRET_KEY'] = 'gaby-moveis-chave-secreta-321'  # Chave para proteger as sessões
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moveis.db'
app.config['UPLOAD_FOLDER'] = 'static/img'

db.init_app(app)

# CONFIGURAÇÃO DO LOGIN MANAGER
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Nome da função da rota de login
login_manager.login_message = "Por favor, faça login para acessar esta página."


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# CRIAÇÃO DO BANCO E USUÁRIO INICIAL
with app.app_context():
    db.create_all()
    # Verifica se já existe um usuário admin, se não, cria um
    if not Usuario.query.filter_by(username='admin').first():
        usuario_admin = Usuario(username='admin', password='admin')  # Altere a senha depois!
        db.session.add(usuario_admin)
        db.session.commit()


# --- ROTAS PÚBLICAS ---

@app.route('/')
def index():
    primeiros_moveis = Movel.query.limit(3).all()
    return render_template('index.html', moveis=primeiros_moveis)


@app.route('/projetos')
def projetos():
    lista_projetos = Movel.query.all()
    return render_template('projetos.html', moveis=lista_projetos)


# --- ROTA DE AUTENTICAÇÃO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = Usuario.query.filter_by(username=username).first()

        if user and user.password == password:  # Comparação direta de senha
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('Usuário ou senha incorretos.')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# --- ROTAS DO PAINEL ADMIN (PROTEGIDAS) ---

@app.route('/admin')
@login_required  # Protege a página de administração
def admin():
    todos = Movel.query.all()
    return render_template('admin.html', moveis=todos)


@app.route('/admin/add', methods=['POST'])
@login_required  # Protege a ação de adicionar
def add_movel():
    nome = request.form.get('nome')
    categoria = request.form.get('categoria')
    descricao = request.form.get('descricao')
    arquivo = request.files.get('imagem')

    if arquivo:
        filename = secure_filename(arquivo.filename)
        arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        novo_movel = Movel()
        novo_movel.nome = nome
        novo_movel.categoria = categoria
        novo_movel.descricao = descricao
        novo_movel.imagem_url = filename

        try:
            novo_movel.preco_base = 0.0
        except AttributeError:
            novo_movel.preco = 0.0

        db.session.add(novo_movel)
        db.session.commit()

    return redirect(url_for('admin'))


@app.route('/admin/delete/<int:id>')
@login_required  # Protege a ação de deletar
def delete_movel(id):
    movel = Movel.query.get(id)
    if movel:
        db.session.delete(movel)
        db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)