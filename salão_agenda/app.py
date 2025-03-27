# app.py
from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from flask_mail import Mail, Message
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'chave-secreta-segura'

# Login da administradora
ADMIN_EMAIL = 'admin@salon.com'
ADMIN_SENHA = '1234'

# Configurações do servidor de e-mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')

mail = Mail(app)

# Inicializa o banco
def init_db():
    with sqlite3.connect('agendamentos.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS agendamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                telefone TEXT,
                email TEXT,
                servico TEXT,
                data TEXT,
                horario TEXT
            )
        ''')

# Função de envio de e-mail
def enviar_email_confirmacao(nome, email, servico, data, horario):
    try:
        msg = Message(
            subject='Confirmação de Agendamento',
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"""Olá {nome},

Seu agendamento para \"{servico}\" foi confirmado para o dia {data} às {horario}.

Qualquer dúvida, estamos à disposição.

Atenciosamente,
Equipe do Salão
"""
        mail.send(msg)
        print(f"[OK] E-mail enviado para {email}")
    except Exception as e:
        print(f"[ERRO] Falha ao enviar e-mail: {e}")

# Página inicial (agendamento)
@app.route("/", methods=["GET", "POST"])
def index():
    sucesso = request.args.get("sucesso") == "1"

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        servico = request.form["servico"]
        data = request.form["data"]
        horario = request.form["horario"]

        try:
            with sqlite3.connect("agendamentos.db") as conn:
                conn.execute("""
                    INSERT INTO agendamentos (nome, telefone, email, servico, data, horario)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (nome, telefone, email, servico, data, horario))
            data_formatada = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
            enviar_email_confirmacao(nome, email, servico, data_formatada, horario)
        except Exception as e:
            print(f"[ERRO] Falha ao registrar agendamento: {e}")

        return redirect("/?sucesso=1")

    return render_template("index.html", sucesso=sucesso)

# Página de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        if email == ADMIN_EMAIL and senha == ADMIN_SENHA:
            session['admin'] = True
            return redirect(url_for("admin"))
        else:
            return render_template("login.html", erro="Credenciais inválidas")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

# Painel administrativo
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    with sqlite3.connect("agendamentos.db") as conn:
        cursor = conn.execute("SELECT * FROM agendamentos ORDER BY data, horario")
        agendamentos_raw = cursor.fetchall()

    # Formata a data no formato dd/mm/yyyy
    agendamentos = []
    for a in agendamentos_raw:
        data_formatada = datetime.strptime(a[5], "%Y-%m-%d").strftime("%d/%m/%Y")
        agendamentos.append((a[0], a[1], a[2], a[3], a[4], data_formatada, a[6]))

    return render_template("admin.html", agendamentos=agendamentos)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
