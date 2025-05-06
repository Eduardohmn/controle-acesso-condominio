from flask import Flask, render_template, request, redirect, url_for, flash
from recognizer.detector import capturar_imagem, detectar_placa
from models.database import Session, Registro, Morador
from models.database import VisitanteFrequente
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
from models.database import VisitanteFrequente

@app.route('/registros', methods=['GET'])
def listar_registros():
    session = Session()
    visitantes_frequentes = session.query(VisitanteFrequente).all()
    frequentes_dict = {v.placa: v.descricao for v in visitantes_frequentes}

    # Filtros (placa, tipo, datas)
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
        query = query.filter(Registro.data_hora >= datetime.strptime(data_inicio, '%Y-%m-%d'))

    if data_fim:
        query = query.filter(Registro.data_hora <= datetime.strptime(data_fim, '%Y-%m-%d'))

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
    
    # Lista de placas frequentes
    placas_frequentes = [v.placa for v in session.query(VisitanteFrequente).all()]
    
    # Deleta todos que não estão na lista de frequentes
    session.query(Registro).filter(Registro.morador_id == None).filter(~Registro.placa.in_(placas_frequentes)).delete(synchronize_session=False)
    
    session.commit()
    session.close()
    
    flash("Visitantes ocasionais apagados com sucesso!", "success")
    return redirect(url_for('listar_registros'))


if __name__ == '__main__':
    app.run(debug=True)
