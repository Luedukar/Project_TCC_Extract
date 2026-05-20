import psycopg2
import os
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ler e priorizar o .env com dados sensíveis
load_dotenv(override=True)


def get_connection():
    """
    Estabelece e retorna uma conexão com o banco de dados PostgreSQL.
    
    Retorna:
        psycopg2.extensions.connection: Conexão com o banco de dados
        
    Em caso de erro:
        psycopg2.Error: Se não conseguir conectar ao banco
    """
    try:
        return psycopg2.connect(
            host=os.getenv("host"),
            database=os.getenv("database"),
            user=os.getenv("user"),
            password=os.getenv("password"),
            port=os.getenv("port"),
        )
    except psycopg2.Error as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        raise

def navegarbanco(product_id):
    """
    Encontra dados de um produto baseado em seu ID.
    
    Recebe:
        product_id: ID do produto a pesquisar
        
    Retorna:
        tuple: Dados do produto 
        ou 
        None se não encontrado
    """
    if not product_id:
        logger.warning("ID do produto não fornecido")
        return None
        
    try:
        with get_connection() as con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM produtos WHERE productID = %s", (product_id,))
                row = cur.fetchone()
                
                if not row:
                    logger.info(f"Produto com ID {product_id} não encontrado")
                    return None
                    
                return row
    except psycopg2.Error as e:
        logger.error(f"Falha ao recuperar dados do produto ID {product_id}: {e}")
        return None

            
def extrairID():
    """
    Extrai todos os IDs de produtos do banco de dados.
    que enviar aviso = true e avisoDiario = false
    extraindo somente os produtos que potencialmente podem receber avisos
    aumentando a eficiencia
    
    Retorna:
        list: Lista contendo todos os IDs de produtos
    """
    try:
        with get_connection() as con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM produtos WHERE enviaraviso = TRUE AND AvisoDiario = FALSE ORDER by productID;")
                return [row[0] for row in cur.fetchall()]
    except psycopg2.Error as e:
        logger.error(f"Falha ao obter IDs de produtos: {e}")
        return []

            
def navegarbancoUsers(user_id):
    """
    Encontra informações de um usuário baseado em seu ID.
    
    Recebe:
        user_id: ID do usuário a pesquisar
        
    Retorna:
        list: Dados do usuário 
        ou 
        lista vazia se não encontrado
    """
    if not user_id:
        logger.warning("ID do usuário não fornecido")
        return []
        
    try:
        with get_connection() as con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                resultado = list(row) if row else []
                return resultado
    except psycopg2.Error as e:
        logger.error(f"Falha ao obter dados do usuário ID {user_id}: {e}")
        return []

            
def avisoEnviado(product_id):
    """
    Marca um produto como com aviso diário enviado para evitar múltiplos envios.
    
    Recebe:
        product_id: ID do produto a ser atualizado
        
    Returna:
        bool: True se atualizado com sucesso 
              False caso contrário
    """
    if not product_id:
        logger.warning("ID do produto não fornecido para avisoEnviado")
        return False
        
    try:
        with get_connection() as con:
            with con.cursor() as cur:
                cur.execute(
                    "UPDATE produtos SET AvisoDiario = TRUE, atualizado = NOW() WHERE productid = %s",
                    (product_id,)
                )
                con.commit()
                logger.info(f"Aviso diário marcado como TRUE para ID: {product_id}")
                return True
    except psycopg2.Error as e:
        logger.error(f"Falha ao atualizar status de AvisoDiario para produto ID {product_id}: {e}")
        return False

def ResetAviso():
    """
    Reseta o status de avisos diários para produtos cuja última atualização foi há mais de 24 horas.
    """
    try:
        with get_connection() as con:
            with con.cursor() as cur:
                cur.execute(
                    "UPDATE produtos SET AvisoDiario = FALSE, atualizado = NOW() "
                    "WHERE AvisoDiario = TRUE AND atualizado < NOW() - INTERVAL '10 minutes';"
                )
                con.commit()
                logger.info(f"Reset de avisos executado. Linhas afetadas: {cur.rowcount}")
                return True
    except psycopg2.Error as e:
        logger.error(f"Falha ao resetar avisos diários: {e}")
        return False
    
def LimparDuploFator():
    """
    Exclui da tabela two_factor_codes os códigos de duplo fator que não são mais utilizados e já estão antigo (24 horas).
    """
    try:
        with get_connection() as con:
            with con.cursor() as cur:
                cur.execute(
                    "DELETE FROM two_factor_codes WHERE mfa_status = FALSE OR attempts >= 3 OR expires_at < NOW();"
                )
                con.commit()
                logger.info(f"Exclusão de 2fa antigos realizada com sucesso. Linhas afetadas: {cur.rowcount}")
                return True
    except psycopg2.Error as e:
        logger.error(f"Falha ao excluir códigos 2fa antigos: {e}")
        return False
    
def LimparUsers():
    """
    Exclui da tabela users os usuarios que foram desativados a mais de 36 horas (3 dias)
    """
    try:
        with get_connection() as con:
            with con.cursor() as cur:
                cur.execute(
                    "DELETE FROM users WHERE status = 'desativado' AND NOW() - datadesativacao >= INTERVAL '5 minutes'"
                )
                con.commit()
                logger.info(f"Exclusão de users desativados realizada com sucesso. Linhas afetadas: {cur.rowcount}")
                return True
    except psycopg2.Error as e:
        logger.error(f"Falha ao excluir users desativados: {e}")
        return False