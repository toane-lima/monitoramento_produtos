import time
import logging
from services.scraper_service import ScraperService

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def rodar_coleta():
    supermercados = ["nordestao", "atacadao", "pao_de_acucar"]
    
    # DICA: Tirei o "Nordestao" do nome do feijão, pois o Atacadão e o Pão de Açúcar
    # não vão encontrar uma marca própria do Nordestão.
    lista_de_compras = ["Arroz Integral Camil", "Feijão Carioca", "Café Pilao"]
    
    scraper = ScraperService()
    
    try:
        # Loop 1: Passa por cada supermercado
        for supermercado in supermercados:
            logging.info(f"\n🛒 === Iniciando coleta no: {supermercado.upper()} ===")
            
            # Loop 2: Busca todos os itens da lista dentro daquele supermercado
            for item in lista_de_compras:
                logging.info(f"Processando: {item}")
                
                # Agora passamos o nome do supermercado para os dois métodos
                if scraper.pesquisar_produto(item, supermercado):
                    time.sleep(3) # Pausa estratégica para a página estabilizar
                    
                    nome, valor = scraper.extrair_primeiro_resultado(supermercado)
                    
                    if nome and valor > 0:
                        scraper.salvar_no_banco(nome, valor)
                    else:
                        logging.warning(f"Dados incompletos para: {item} no {supermercado}")
                
                time.sleep(3) # Intervalo entre buscas para imitar um humano
                
    except Exception as e:
        logging.error(f"Erro inesperado no orquestrador: {e}")
    finally:
        scraper.fechar()
        logging.info("\n✅ Coleta finalizada em todos os supermercados.")

if __name__ == "__main__":
    rodar_coleta()