import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from database.connection import SessionLocal
from database.models import Produto, RegistroPreco, Supermercado

class ScraperService:
    def __init__(self):
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def pesquisar_produto(self, termo: str, supermercado: str):
        try:
            if supermercado.lower() == "nordestao":
                termo_formatado = termo.replace(" ", "%20")
                url = f"https://www.nordestaomaisvoce.com.br/busca?termo={termo_formatado}"
                self.driver.get(url)
                time.sleep(5)
                return True
                
            elif supermercado.lower() == "atacadao":
                termo_formatado = termo.replace(" ", "+")
                url = f"https://www.atacadao.com.br/s?q={termo_formatado}"
                self.driver.get(url)
                time.sleep(5)
                return True
                
            elif supermercado.lower() == "pao_de_acucar":
                termo_formatado = termo.replace(" ", "%20")
                url = f"https://www.paodeacucar.com/busca?terms={termo_formatado}"
                self.driver.get(url)
                time.sleep(5)
                return True
                
            return False
        except Exception as e:
            print(f"❌ Erro ao acessar busca no {supermercado}: {e}")
            return False

    def extrair_primeiro_resultado(self, supermercado: str):
        try:
            wait = WebDriverWait(self.driver, 15)
            nome = ""
            preco_texto = ""
            
            if supermercado.lower() == "nordestao":
                nome_elemento = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-cy='produto-descricao']")))
                nome = nome_elemento.text.strip()
                preco_elemento = self.driver.find_element(By.CSS_SELECTOR, "[data-cy='preco']")
                preco_texto = preco_elemento.text.strip()
                
            elif supermercado.lower() == "atacadao":
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article")))
                cards = self.driver.find_elements(By.CSS_SELECTOR, "article")
                
                produto_organico = None
                for card in cards:
                    if "PATROCINADO" not in card.text.upper():
                        produto_organico = card
                        break
                
                if not produto_organico:
                    return None, 0.0
                    
                nome_elemento = produto_organico.find_element(By.CSS_SELECTOR, "[data-testid='product-link']")
                nome = nome_elemento.get_attribute("title").strip()
                preco_elemento = produto_organico.find_element(By.XPATH, ".//p[contains(text(), 'R$')]")
                preco_texto = preco_elemento.text.strip()
                
            elif supermercado.lower() == "pao_de_acucar":
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='Card-sc']")))
                
                primeiro_card = self.driver.find_element(By.CSS_SELECTOR, "div[class*='Card-sc']")
                
                nome_elemento = primeiro_card.find_element(By.CSS_SELECTOR, "a[class*='Title-sc']")
                
                nome = nome_elemento.get_attribute("title")
                if not nome:
                    nome = nome_elemento.text.strip()
                    
                preco_elemento = primeiro_card.find_element(By.CSS_SELECTOR, "[class*='PriceValue']")
                preco_texto = preco_elemento.text.strip()
            
            else:
                return None, 0.0

            if not nome or not preco_texto:
                return None, 0.0

            preco_limpo = preco_texto.replace('R$', '').replace('.', '').replace(',', '.').strip()
            preco_limpo = preco_limpo.split()[0]
            valor = float(preco_limpo)
            
            print(f"✅ Extraído [{supermercado}]: {nome} | R$ {valor}")
            return nome, valor
            
        except Exception as e:
            return None, 0.0

    def salvar_no_banco(self, nome_produto: str, valor: float, nome_supermercado: str):
        session = SessionLocal()
        try:
            mercado = session.query(Supermercado).filter_by(nome=nome_supermercado).first()
            if not mercado:
                mercado = Supermercado(nome=nome_supermercado)
                session.add(mercado)
                session.commit() # Commita para gerar o ID do mercado

            produto = session.query(Produto).filter_by(nome=nome_produto).first()
            if not produto:
                produto = Produto(nome=nome_produto, categoria="Geral")
                session.add(produto)
                session.commit() # Commita para gerar o ID do produto
            
            novo_preco = RegistroPreco(
                valor=valor, 
                produto_id=produto.id, 
                supermercado_id=mercado.id
            )
            session.add(novo_preco)
            session.commit()
            print(f"✅ Salvo: {nome_produto} | {nome_supermercado} | R$ {valor}")
        except Exception as e:
            session.rollback()
            print(f"❌ ERRO AO SALVAR: {e}")
        finally:
            session.close()

    def fechar(self):
        self.driver.quit()