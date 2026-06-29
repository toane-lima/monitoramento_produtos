from database.connection import SessionLocal
from database.models import Produto

def testar_conexao():
    # Cria uma sessão com o banco
    session = SessionLocal()
    
    try:
        # 1. Tenta salvar um produto de teste
        novo_produto = Produto(nome="Teste Monitoramento", categoria="Eletrônicos")
        session.add(novo_produto)
        session.commit()
        print("✅ Produto inserido com sucesso!")

        # 2. Tenta buscar o produto no banco
        produto_db = session.query(Produto).filter_by(nome="Teste Monitoramento").first()
        if produto_db:
            print(f"✅ Conectividade confirmada! Produto encontrado: {produto_db.nome} (ID: {produto_db.id})")
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        
    finally:
        session.close()

if __name__ == "__main__":
    testar_conexao()