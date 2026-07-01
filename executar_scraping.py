import time
import logging
import datetime

from services.scraper_service import ScraperService
from database.connection import SessionLocal
from database.models import Monitoramento, MonitoramentoItem

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def buscar_produtos_ativos(usuario_id=None):
    """
    Busca produtos de monitoramentos ativos.
    Se usuario_id for informado, busca apenas produtos daquele usuário.
    """
    session = SessionLocal()
    hoje = datetime.date.today()

    try:
        query = (
            session.query(MonitoramentoItem.produto_nome)
            .join(Monitoramento, Monitoramento.id == MonitoramentoItem.monitoramento_id)
            .filter(Monitoramento.ativo == True)
            .filter(Monitoramento.data_inicio <= hoje)
            .filter(Monitoramento.data_fim >= hoje)
        )

        if usuario_id:
            query = query.filter(Monitoramento.usuario_id == usuario_id)

        registros = query.distinct().all()

        return [r[0] for r in registros]

    finally:
        session.close()


def desativar_monitoramentos_expirados():
    """
    Desativa listas cujo prazo já acabou.
    """
    session = SessionLocal()
    hoje = datetime.date.today()

    try:
        expirados = (
            session.query(Monitoramento)
            .filter(Monitoramento.ativo == True)
            .filter(Monitoramento.data_fim < hoje)
            .all()
        )

        for monitoramento in expirados:
            monitoramento.ativo = False

        session.commit()

    except Exception as e:
        session.rollback()
        logging.error(f"Erro ao desativar monitoramentos expirados: {e}")

    finally:
        session.close()


def rodar_coleta(usuario_id=None, produtos=None):
    """
    Roda a coleta de preços.

    Uso 1 - Coleta agendada:
        rodar_coleta()

    Uso 2 - Coleta manual do usuário logado:
        rodar_coleta(usuario_id=st.session_state.usuario_id)

    Uso 3 - Coleta manual de uma lista específica:
        rodar_coleta(produtos=["Arroz", "Feijão"])
    """
    supermercados = ["nordestao", "atacadao", "pao_de_acucar"]

    desativar_monitoramentos_expirados()

    if produtos is None:
        lista_de_compras = buscar_produtos_ativos(usuario_id=usuario_id)
    else:
        lista_de_compras = [p.strip() for p in produtos if p and p.strip()]

    resumo = {
        "produtos": len(lista_de_compras),
        "tentativas": 0,
        "sucessos": 0,
        "falhas": 0,
    }

    if not lista_de_compras:
        logging.info("Nenhum produto ativo para monitoramento.")
        return resumo

    logging.info(f"Produtos para coleta: {lista_de_compras}")

    scraper = ScraperService()

    try:
        for supermercado in supermercados:
            logging.info(f"\n🛒 === Iniciando coleta no: {supermercado.upper()} ===")

            for item in lista_de_compras:
                resumo["tentativas"] += 1
                logging.info(f"Processando: {item}")

                if scraper.pesquisar_produto(item, supermercado):
                    time.sleep(3)

                    nome_raspado, valor = scraper.extrair_primeiro_resultado(supermercado)

                    if nome_raspado and valor > 0:
                        scraper.salvar_no_banco(item, valor, supermercado)
                        resumo["sucessos"] += 1
                        logging.info(
                            f"✅ Padronizado: site retornou '{nome_raspado}', "
                            f"mas salvamos como '{item}'"
                        )
                    else:
                        resumo["falhas"] += 1
                        logging.warning(f"Dados incompletos para: {item} no {supermercado}")
                else:
                    resumo["falhas"] += 1
                    logging.warning(f"Não foi possível pesquisar: {item} no {supermercado}")

                time.sleep(3)

    except Exception as e:
        logging.error(f"Erro inesperado no orquestrador: {e}")

    finally:
        scraper.fechar()
        logging.info("\n✅ Coleta finalizada em todos os supermercados.")

    return resumo


if __name__ == "__main__":
    resultado = rodar_coleta()
    print(resultado)