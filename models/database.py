from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class Morador(Base):
    __tablename__ = 'moradores'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    endereco = Column(String, nullable=False)
    telefone = Column(String)
    placa = Column(String, nullable=False)

class Registro(Base):
    __tablename__ = 'registros'
    
    id = Column(Integer, primary_key=True)
    placa = Column(String, nullable=False)
    morador_id = Column(Integer, ForeignKey('moradores.id'))  # FK opcional
    data_hora = Column(DateTime, default=datetime.datetime.utcnow)
    tipo = Column(String, nullable=False)  # entrada ou saída
    imagem_rg = Column(String)  # Caminho do arquivo de RG do visitante

class VisitanteFrequente(Base):
    __tablename__ = 'visitantes_frequentes'
    
    id = Column(Integer, primary_key=True)
    placa = Column(String, unique=True, nullable=False)
    descricao = Column(String)  # Ex: "Correios", "Entregador fixo", etc.


# Conexão com o banco SQLite
engine = create_engine('sqlite:///condominio.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
