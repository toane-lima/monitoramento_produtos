import sys
import os
sys.path.append(os.path.abspath(os.curdir))
from database.connection import engine, Base
# Importar modelos garante que o Base saiba quais tabelas criar
from database.models import Produto, RegistroPreco 

print("Limpando e recriando tabelas...")
Base.metadata.drop_all(engine) # Apaga as tabelas antigas (limpeza segura)
Base.metadata.create_all(engine) # Cria as tabelas novas com a estrutura correta
print("Banco de dados pronto!")