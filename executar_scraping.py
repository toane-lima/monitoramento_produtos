import time
import logging
from services.scraper_service import ScraperService

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def rodar_coleta():
    supermercados = ["nordestao", "atacadao", "pao_de_acucar"]
    
    lista_de_compras = ["Arroz Integral Camil", "Feijão Carioca", "Café Pilao"]
    
    scraper = ScraperService()
    
    try:
        for supermercado in supermercados:
            logging.info(f"\n🛒 === Iniciando coleta no: {supermercado.upper()} ===")
            
            for item in lista_de_compras:
                logging.info(f"Processando: {item}")
                
                if scraper.pesquisar_produto(item, supermercado):
                    time.sleep(3) # Pausa estratégica para a página estabilizar
                    
                    nome_raspado, valor = scraper.extrair_primeiro_resultado(supermercado)
                    
                    if nome_raspado and valor > 0:
                        scraper.salvar_no_banco(item, valor, supermercado) 
                        print(f"✅ Padronizado: O site retornou '{nome_raspado}', mas salvamos como '{item}'")
                    else:
                        logging.warning(f"Dados incompletos para: {item} no {supermercado}")
                
                time.sleep(3)
                
    except Exception as e:
        logging.error(f"Erro inesperado no orquestrador: {e}")
    finally:
        scraper.fechar()
        logging.info("\n✅ Coleta finalizada em todos os supermercados.")

if __name__ == "__main__":
    rodar_coleta()