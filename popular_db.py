from sqlalchemy import create_engine
from models.database import Base, Session, Morador, Carro, Registro, VisitanteFrequente
from datetime import datetime, timedelta
import pytz
import random
import os

# Recria o banco
engine = create_engine('sqlite:///condominio.db')
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
session = Session()

fuso = pytz.timezone("America/Sao_Paulo")
agora = datetime.now(fuso)

# --- MORADORES + CARROS ---
moradores_data = [
    ("Carlos Andrade", "Rua Alpha, 101", "11999999999", ["ABC1234", "DEF5678"]),
    ("Fernanda Lima", "Rua Beta, 202", "11988888888", ["GHI9012"]),
    ("João Pedro", "Rua Gamma, 303", "11977777777", ["JKL3456", "MNO7890"]),
    ("Ana Beatriz", "Rua Delta, 404", "11966666666", ["ZXC9876"]),
    ("Rafael Torres", "Rua Épsilon, 505", "11955555555", ["QWE4321", "ASD8765"]),
    ("Larissa Souza", "Rua Zeta, 606", "11944444444", ["TYU1234"]),
    ("Marcos Vinicius", "Rua Eta, 707", "11933333333", ["BNM6789"]),
    ("Juliana Alves", "Rua Theta, 808", "11922222222", ["PLM2345"]),
    ("Gabriel Costa", "Rua Iota, 909", "11911111111", ["XCV5432"]),
    ("Isabela Rocha", "Rua Kappa, 1001", "11900000000", ["HJK7654"])
]

for nome, endereco, telefone, placas in moradores_data:
    morador = Morador(nome=nome, endereco=endereco, telefone=telefone)
    session.add(morador)
    session.flush()
    for placa in placas:
        session.add(Carro(placa=placa, morador_id=morador.id))

# --- VISITANTES FREQUENTES ---
visitantes = [
    ("PQR1234", "Uber - Maria"),
    ("STU5678", "Entregador Mercado Livre"),
    ("VWX9012", "Técnico de Internet"),
    ("LMN3456", "Vigilância Patrimonial"),
    ("YZA6543", "Manutenção Elétrica"),
    ("BCD7890", "Síndico visitante")
]
for placa, desc in visitantes:
    session.add(VisitanteFrequente(placa=placa, descricao=desc))

# --- REGISTROS DE VISITANTES (ocasionais) ---
placas_ocasionais = ["ZZZ0001", "XYZ2222", "QWE3333", "AAA1111", "BBB2222", "CCC3333", "DDD4444", "EEE5555", "FFF6666", "GGG7777", "HHH8888", "III9999", "JJJ0000", "KKK1111", "LLL2222"]

os.makedirs("static/captures/rg_fotos", exist_ok=True)

for i, placa in enumerate(placas_ocasionais):
    registro = Registro(
        placa=placa,
        tipo="entrada" if i % 2 == 0 else "saida",
        data_hora=agora - timedelta(days=i),
        imagem_rg=f"captures/rg_fotos/rg_teste_{i}.jpg" if i % 3 == 0 else None
    )
    session.add(registro)

session.commit()
session.close()
print("✅ Banco de dados populado com dados ricos e variados.")
