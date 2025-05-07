from flask import Flask, render_template, request, redirect, url_for, flash, Response
from recognizer.detector import detectar_placa
from models.database import Session, Registro, Morador, VisitanteFrequente
import datetime
import cv2

app = Flask(__name__)
app.secret_key = 's3cr3t'

# Inicializa a câmera global
camera = cv2.VideoCapture(0)

# Captura de imagem ao vivo (sem importar detector.py)
def capturar_imagem():
    ret, frame = camera.read()
    if ret:
        cv2.imwrite('static/captures/captura.jpg', frame)

# Stream em tempo real para o <img src="/video_feed">
def gerar_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

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

@app.route('/registros', methods=['GET'])
def listar_registros():
    session = Session()
    visitantes_frequentes = session.query(VisitanteFrequente).all()
    frequentes_dict = {v.placa: v.descricao for v in visitantes_frequentes}

    placa = request.args.get('placa', '').upper()
    tipo = request.args.get('tipo', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')

    query = session.query(Registro).filter(Registro.morador_id == None)

    if placa:
        query = query.filter(Registro.placa.like(f'%{placa}%'))
    if tipo in ['entrada', 'saida']:
        query = query.filter(Registro.tipo == tipo)
    if data_inicio:
        query = query.filter(Registro.data_hora >= datetime.datetime.strptime(data_inicio, '%Y-%m-%d'))
    if data_fim:
        query = query.filter(Registro.data_hora <= datetime.datetime.strptime(data_fim, '%Y-%m-%d'))

    registros = query.order_by(Registro.data_hora.desc()).all()
    session.close()

    return render_template('registros.html', registros=registros, frequentes=frequentes_dict)

@app.route('/visitantes_frequentes', methods=['GET', 'POST'])
def visitantes_frequentes():
    session = Session()
    if request.method == 'POST':
        placa = request.form['placa'].upper().replace(" ", "").replace("-", "")
        descricao = request.form['descricao']
        if not session.query(VisitanteFrequente).filter_by(placa=placa).first():
            novo = VisitanteFrequente(placa=placa, descricao=descricao)
            session.add(novo)
            session.commit()
    lista = session.query(VisitanteFrequente).all()
    session.close()
    return render_template('visitantes_frequentes.html', lista=lista)

@app.route('/remover_visitante_frequente/<int:id>', methods=['POST'])
def remover_visitante_frequente(id):
    session = Session()
    visitante = session.query(VisitanteFrequente).get(id)
    if visitante:
        session.delete(visitante)
        session.commit()
    session.close()
    return redirect(url_for('visitantes_frequentes'))

@app.route('/apagar_ocasionais')
def apagar_ocasionais():
    session = Session()
    placas_frequentes = [v.placa for v in session.query(VisitanteFrequente).all()]
    session.query(Registro)\
        .filter(Registro.morador_id == None)\
        .filter(~Registro.placa.in_(placas_frequentes))\
        .delete(synchronize_session=False)
    session.commit()
    session.close()
    flash("Visitantes ocasionais apagados com sucesso!", "success")
    return redirect(url_for('listar_registros'))

@app.route('/video_feed')
def video_feed():
    return Response(gerar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
