from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bf
import time as tm
import EnviarGmail as gm
import schedule
from schedule import repeat, every
import ConnectBanco as cb
import Funcoes
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


#loop para a função principal (execuções em um intervalor de 8 horas)
@repeat(every(3).minutes)

def main():
    #extrair todos os IDs de produtos
    idsProduto = cb.extrairID()

    #para cada ID extraido, executa a busca
    for id in idsProduto:

        #Extrai as informações do produto com base em seu ID
        listProduto = cb.navegarbanco(id)

        #O link do produto vem na quarta posição (5º elemento) do array retornado
        link = listProduto[4]

        #Abre o navegador (Chrome) e busca pela pagina do link
        driver = webdriver.Chrome()
        driver.get(link)

        #Espera o site carregar
        tm.sleep(5)

        #Ler o HTML da pagina
        site = bf(driver.page_source, "html.parser")

        #lista para preços (inicialmente vazia)
        preco= []

        #Extrair valor principal (melhor valor normalmente ou mais recomendado)
        valores1 = site.find('span', class_='aok-offscreen')

        #Extrair outras opções de valores
        valores2 = site.find_all('span', class_="olpWrapper a-size-small")

        #incluir em "preco" o valor obtido em "valores1" (apenas 1 valor)
        preco.append(valores1)

        #Incluir em "preco" o valor obtido em "valores2" (mais de 1 valor)
        for i in valores2:
            preco.append(i)

        #Fecha o drive
        driver.quit()

        #Lista Vazia para armazenar os preços processados
        precos_encontrados = []
        
        #percorre todos os itens de preco e realiza uma higienização
        for tag in preco:
            texto = tag.get_text() if hasattr(tag, 'get_text') else str(tag)
            valor = Funcoes.extrair_preco_de_texto(texto)
            if valor is not None:
                precos_encontrados.append(valor)
        
        #Encontra o menor preço na lista (objetivo), se for igual ou inferior ao preço desejado, envia o email
        if precos_encontrados:
            if min(precos_encontrados) <= listProduto[3]:
                logger.info(f"O preço desejado ou inferior foi encontrado para o produto de ID: {id}")
                listUser = cb.navegarbancoUsers(listProduto[1])
                gm.dispararEmail(listUser[1], listUser[3], listProduto[2], listProduto[4], listProduto[3])
        else:
            #Caso não tenha sido encontrado nenhum preço
            logger.warning(f"Nenhum preço encontrado para o produto de ID: {id}")
        
        #Fim do loop
        tm.sleep(30)
    
    logger.info("fim do loop")

while True:
    schedule.run_pending()
    tm.sleep(1)
