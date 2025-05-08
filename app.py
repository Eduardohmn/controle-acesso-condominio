from flask import Flask, render_template, request, redirect, url_for, flash, Response
from recognizer.detector import detectar_placa
from models.database import Session, Registro, Morador, VisitanteFrequente
import cv2
from datetime import datetime
import pytz
import threading
import time
import os
from flask import render_template, request, redirect, url_for, flash
from models.database import Session, Morador, Carro
from sqlalchemy.orm import joinedload


app = Flask(__name__)
app.secret_key = 's3cr3t'

fuso_brasil = pytz.timezone("America/Sao_Paulo")

camera = cv2.VideoCapture(0)
camera_lock = threading.Lock()

ultima_placa_nao_registrada = {
    "placa": None,
    "registro_id": None
}

def gerar_frames():
    while True:
        with camera_lock:
            success, frame = camera.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html', placas=None, avisos=[])

@app.route('/capturar', methods=['POST'])
def capturar():
    avisos = []
    with camera_lock:
        ret, frame = camera.read()

    if not ret:
        flash("Erro ao acessar a câmera!", "danger")
        return redirect(url_for('index'))

    caminho = 'static/captures/temp_captura.jpg'
    cv2.imwrite(caminho, frame)
    placas_detectadas = detectar_placa(caminho)

    session = Session()

    if placas_detectadas:
        for placa in placas_detectadas:
            placa = placa.upper().replace("-", "").replace(" ", "")
            carro = session.query(Carro).filter_by(placa=placa).first()
            frequente = session.query(VisitanteFrequente).filter_by(placa=placa).first()

            if carro:
                avisos.append(f'✅ {placa} autorizada — morador registrado.')
            elif frequente:
                avisos.append(f'✅ {placa} autorizada — visitante frequente ({frequente.descricao}).')

            if not carro and not frequente:
                ja_registrado = session.query(Registro).filter_by(placa=placa).order_by(Registro.id.desc()).first()
                agora = datetime.now(fuso_brasil)

                if not ja_registrado or (agora - ja_registrado.data_hora.replace(tzinfo=fuso_brasil)).seconds > 10:
                    novo = Registro(
                        placa=placa,
                        morador_id=None,
                        tipo='entrada',
                        data_hora=agora,
                        imagem_rg=None
                    )
                    session.add(novo)
                    session.commit()
                    ultima_placa_nao_registrada["placa"] = placa
                    ultima_placa_nao_registrada["registro_id"] = novo.id

                avisos.append(f'⚠️ {placa} não registrada — visitante adicionado, favor verificar RG.')
    else:
        registro_id = ultima_placa_nao_registrada.get("registro_id")
        if not registro_id:
            avisos.append("❌ Nenhuma placa detectada e nenhum visitante recente para associar o RG.")
            session.close()
            return render_template('index.html', placas=[], avisos=avisos)

        nome_arquivo = f"rg_{registro_id}_{datetime.now(fuso_brasil).strftime('%Y%m%d%H%M%S')}.jpg"
        caminho_relativo = f'captures/rg_fotos/{nome_arquivo}'
        caminho_completo = f'static/{caminho_relativo}'
        os.makedirs('static/captures/rg_fotos', exist_ok=True)
        cv2.imwrite(caminho_completo, frame)

        registro = session.query(Registro).get(registro_id)
        if registro:
            registro.imagem_rg = caminho_relativo
            session.commit()
            avisos.append(f"📄 RG associado ao visitante {registro.placa}.")

    session.close()
    return render_template('index.html', placas=placas_detectadas, avisos=avisos)


@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_morador():
    session = Session()

    if request.method == 'POST':
        nome = request.form['nome']
        endereco = request.form['endereco']
        telefone = request.form['telefone']
        placas = request.form.getlist('placas')

        # Cria o morador
        novo = Morador(nome=nome, endereco=endereco, telefone=telefone)
        session.add(novo)
        session.flush()  # para obter o novo.id

        # Adiciona os carros
        for placa in placas:
            placa_formatada = placa.upper().replace(" ", "").replace("-", "")
            carro = Carro(placa=placa_formatada, morador_id=novo.id)
            session.add(carro)

        session.commit()
        flash('Morador e carros cadastrados com sucesso!', 'success')
        session.close()
        return redirect(url_for('cadastrar_morador'))

    return render_template('cadastro.html')

@app.route('/registros')
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
        dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').replace(tzinfo=fuso_brasil)
        query = query.filter(Registro.data_hora >= dt_inicio)
    if data_fim:
        dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(tzinfo=fuso_brasil)
        query = query.filter(Registro.data_hora <= dt_fim)

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
    session.query(Registro).filter(
        Registro.morador_id == None,
        ~Registro.placa.in_(placas_frequentes)
    ).delete(synchronize_session=False)
    session.commit()
    session.close()
    flash("Visitantes ocasionais apagados com sucesso!", "success")
    return redirect(url_for('listar_registros'))

@app.route('/video_feed')
def video_feed():
    return Response(gerar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/moradores')
def listar_moradores():
    session = Session()
    moradores = session.query(Morador).options(joinedload(Morador.carros)).all()
    session.close()
    return render_template('moradores.html', moradores=moradores)



@app.route('/remover_morador/<int:id>', methods=['POST'])
def remover_morador(id):
    session = Session()
    morador = session.query(Morador).get(id)
    if morador:
        session.delete(morador)
        session.commit()
    session.close()
    flash('Morador removido com sucesso!', 'success')
    return redirect(url_for('listar_moradores'))  # <- redireciona para a lista


@app.route('/editar_morador/<int:id>', methods=['POST'])
def editar_morador(id):
    session = Session()
    morador = session.query(Morador).get(id)

    if not morador:
        session.close()
        return "Morador não encontrado", 404

    data = request.get_json()
    morador.nome = data.get('nome', morador.nome)
    morador.endereco = data.get('endereco', morador.endereco)
    morador.telefone = data.get('telefone', morador.telefone)
    session.commit()
    session.close()
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True)
