from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pytz
from datetime import datetime

Base = declarative_base()
fuso_brasil = pytz.timezone("America/Sao_Paulo")

def now_brasil():
    return datetime.now(fuso_brasil)

class Morador(Base):
    __tablename__ = 'moradores'

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    endereco = Column(String, nullable=False)
    telefone = Column(String)
    carros = relationship("Carro", cascade="all, delete-orphan", back_populates="morador")

class Carro(Base):
    __tablename__ = 'carros'

    id = Column(Integer, primary_key=True)
    placa = Column(String, nullable=False, unique=True)
    morador_id = Column(Integer, ForeignKey('moradores.id'))
    morador = relationship("Morador", back_populates="carros")

class Registro(Base):
    __tablename__ = 'registros'

    id = Column(Integer, primary_key=True)
    placa = Column(String, nullable=False)
    morador_id = Column(Integer, ForeignKey('moradores.id'))  # FK opcional
    data_hora = Column(DateTime(timezone=True), default=now_brasil)
    tipo = Column(String, nullable=False)  # entrada ou saída
    imagem_rg = Column(String)

class VisitanteFrequente(Base):
    __tablename__ = 'visitantes_frequentes'

    id = Column(Integer, primary_key=True)
    placa = Column(String, unique=True, nullable=False)
    descricao = Column(String)

# Conexão com o banco SQLite
engine = create_engine('sqlite:///condominio.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
