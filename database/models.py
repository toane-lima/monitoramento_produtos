import uuid
import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, registry
from database.connection import Base

class Produto(Base):
    __tablename__ = 'produtos'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    categoria = Column(String)
    
    precos = relationship("RegistroPreco", back_populates="produto")
    
    def getNome(self) -> str:
        return self.nome

    def getCategoria(self) -> str:
        return self.categoria

    def validarDados(self) -> bool:
        return bool(self.nome and self.categoria)

class Supermercado(Base):
    __tablename__ = 'supermercados'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    localidade = Column(String)
    catalogo_online = Column(Boolean, default=True)

    def getNome(self) -> str:
        return self.nome

    def getLocalidade(self) -> str:
        return self.localidade

class RegistroPreco(Base):
    __tablename__ = 'registros_preco'
    
    id = Column(Integer, primary_key=True)
    valor = Column(Float, nullable=False)
    data_coleta = Column(DateTime, default=datetime.datetime.utcnow)
    
    produto_id = Column(Integer, ForeignKey('produtos.id'))
    produto = relationship("Produto", back_populates="precos")

    supermercado_id = Column(Integer, ForeignKey('supermercados.id'))
    supermercado = relationship("Supermercado")

    def setPreco(self, valor: float) -> None:
        self.valor = valor

    def getHistorico(self) -> list:
        return []

    def calcularMenorPreco(self) -> None:
        pass

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)
    status_monitoramento = Column(Boolean, default=True, nullable=False)
    data_cadastro = Column(Date, default=datetime.date.today, nullable=False)
    listas = relationship("ListaCompras", back_populates="usuario")

    def salvarLista(self) -> list:
        return []

    def removerItem(self, item_id: int) -> str:
        return "Item removido"

    def cadastrarUsuario(self) -> bool:
        return True

    def atualizarPerfil(self) -> bool:
        return True

    def desativarConta(self) -> bool:
        self.status_monitoramento = False
        return True

    def autenticar(self, email: str, senha: str) -> bool:
        return self.email == email and self.senha == senha

class ListaCompras(Base):
    __tablename__ = "lista_compras"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    produto_nome = Column(String) # O nome do produto que ele quer monitorar
    
    usuario = relationship("Usuario", back_populates="listas")

mapper_registry = registry()
mapper_registry.configure()

class Monitoramento(Base):
    __tablename__ = "monitoramentos"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    nome_lista = Column(String, nullable=False)
    data_inicio = Column(Date, default=datetime.date.today, nullable=False)
    data_fim = Column(Date, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    coletas_por_dia = Column(Integer, default=4, nullable=False)
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)

    usuario = relationship("Usuario")
    itens = relationship("MonitoramentoItem", back_populates="monitoramento")


class MonitoramentoItem(Base):
    __tablename__ = "monitoramento_itens"

    id = Column(Integer, primary_key=True)
    monitoramento_id = Column(Integer, ForeignKey("monitoramentos.id"), nullable=False)
    produto_nome = Column(String, nullable=False)

    monitoramento = relationship("Monitoramento", back_populates="itens")