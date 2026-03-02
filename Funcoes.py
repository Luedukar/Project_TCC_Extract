import re

#Função para extrair or valores em meio ao texto 
def extrair_preco_de_texto(texto):
    # encontra padrões como 3.599,04 ou 3299,00
    matches = re.findall(r'\d{1,3}(?:\.\d{3})*(?:,\d{2})', texto)
    if not matches:
        return None
    s = matches[-1]
    s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None