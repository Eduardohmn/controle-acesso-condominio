from flask import Flask, render_template, request, redirect, url_for, flash
from recognizer.detector import capturar_imagem, detectar_placa
from models.database import Session, Registro, Morador
import datetime

app = Flask(__name__)
app.secret_key = 's3cr3t'  # Para mensagens flash

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', placas=None)

@app.route('/capturar', methods=['POST'])
def capturar():
    capturar_imagem()
    placas_detectadas = detectar_placa('static/captures/captura.jpg')

    session = Session()
    for placa in placas_detectadas:
        registro = Registro(
            placa=placa,
            morador_id=None,
            tipo='entrada',
            data_hora=datetime.datetime.utcnow()
        )
        session.add(registro)
    session.commit()
    session.close()

    return render_template('index.html', placas=placas_detectadas)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_morador():
    if request.method == 'POST':
        nome = request.form['nome']
        endereco = request.form['endereco']
        telefone = request.form['telefone']
        placa = request.form['placa'].upper().replace(" ", "").replace("-", "")
        
        session = Session()
        existente = session.query(Morador).filter_by(placa=placa).first()
        if existente:
            flash('Essa placa já está cadastrada para outro morador!', 'danger')
        else:
            novo = Morador(nome=nome, endereco=endereco, telefone=telefone, placa=placa)
            session.add(novo)
            session.commit()
            flash('Morador cadastrado com sucesso!', 'success')
        session.close()
        return redirect(url_for('cadastrar_morador'))
    
    return render_template('cadastro.html')
@app.route('/registros')
def listar_registros():
    session = Session()
    registros = session.query(Registro).filter(Registro.morador_id == None).order_by(Registro.data_hora.desc()).all()
    session.close()
    return render_template('registros.html', registros=registros)

if __name__ == '__main__':
    app.run(debug=True)
