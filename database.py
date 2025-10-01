# aplicacao_web_atendimento/database.py

import mysql.connector
from mysql.connector import Error
from flask import g  # Importa o 'g', o contexto global da requisição
from config import DB_CONFIG
from datetime import date, timedelta 

def get_db_connection():
    """Cria e retorna uma NOVA conexão com o banco de dados."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def get_lojas_ativas():
    """Busca lojas usando a conexão da requisição atual (g.db)."""
    conn = g.db
    if conn is None: return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("USE drogamais")
        query = "SELECT LOJA_NUMERO, FANTASIA FROM tb_loja WHERE ATIVO = 1 AND LOJA_NUMERO IS NOT NULL AND LOJA_NUMERO > 0 ORDER BY LOJA_NUMERO"
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(f"Erro ao buscar lojas: {e}")
        return []
    finally:
        cursor.close()

def save_new_atendimentos(registros):
    """Salva atendimentos usando a conexão da requisição atual (g.db)."""
    conn = g.db
    if conn is None: return 0, "Erro de conexão com o banco de dados."

    cursor = conn.cursor()
    sql_insert = """
        INSERT INTO tb_atendimentos (chave_id, data, tarefa, responsavel, funcao, loja, tipo, acao, assunto)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.executemany(sql_insert, registros)
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()
        
def get_atendimentos_para_editar(sql_query, params):
    """Busca atendimentos usando a conexão da requisição atual (g.db)."""
    conn = g.db
    if conn is None: return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql_query, tuple(params))
        return cursor.fetchall()
    except Error as e:
        print(f"Erro ao buscar atendimentos: {e}")
        return []
    finally:
        cursor.close()

def insert_atendimentos(cursor, registros):
    """Prepara e executa a inserção para a tabela tb_atendimentos."""
    sql_insert = """
        INSERT INTO tb_atendimentos (chave_id, data, tarefa, responsavel, funcao, loja, tipo, acao, assunto)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(sql_insert, registros)
    return cursor.rowcount

def insert_atendimentos_massa(cursor, registros):
    """
    Prepara e executa a inserção para a tabela tb_atendimentos_massa.
    Agora inclui a coluna id_massa para vincular ao registro resumo.
    """
    sql_insert = """
        INSERT INTO tb_atendimentos_massa (chave_id, id_massa, data, tarefa, responsavel, funcao, loja, tipo, acao, assunto)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(sql_insert, registros)
    return cursor.rowcount

def get_atendimentos_massa_para_deletar():
    """
    Busca os registros de resumo e, em uma segunda etapa, conta as lojas associadas.
    Este método é mais robusto e evita problemas de compatibilidade com SQL.
    """
    conn = g.db
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        query_resumos = "SELECT * FROM tb_atendimentos WHERE loja = -1 AND status = 'ATIVO' ORDER BY data DESC, chave_id DESC"
        cursor.execute(query_resumos)
        atendimentos = cursor.fetchall()

        if not atendimentos:
            return []

        # Etapa 2: Contar as lojas para cada registro de resumo encontrado.
        ids_massa = [a['chave_id'] for a in atendimentos]
        
        # Prepara a query de contagem para todos os IDs de uma vez
        format_strings = ','.join(['%s'] * len(ids_massa))
        query_contagem = f"""
            SELECT id_massa, COUNT(chave_id) as total_lojas 
            FROM tb_atendimentos_massa 
            WHERE id_massa IN ({format_strings}) 
            GROUP BY id_massa
        """
        cursor.execute(query_contagem, tuple(ids_massa))
        contagens = cursor.fetchall()

        # Mapeia os IDs para suas contagens para acesso rápido
        mapa_contagens = {c['id_massa']: c['total_lojas'] for c in contagens}

        # Adiciona a contagem a cada registro de atendimento
        for atendimento in atendimentos:
            atendimento['total_lojas'] = mapa_contagens.get(atendimento['chave_id'], 0)

        return atendimentos

    except Error as e:
        print(f"Erro ao buscar atendimentos em massa para deletar: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

def soft_delete_atendimentos_massa(ids_para_desativar):
    """
    Realiza um SOFT DELETE. Altera o status dos registros para 'DELETADO'
    em vez de apagar permanentemente.
    """
    conn = g.db
    if conn is None: return 0, "Erro de conexão com o banco de dados."

    cursor = conn.cursor()
    try:
        format_strings = ','.join(['%s'] * len(ids_para_desativar))

        # Atualiza o status na tabela de detalhes (massa)
        sql_update_massa = f"UPDATE tb_atendimentos_massa SET status = 'DELETADO' WHERE id_massa IN ({format_strings})"
        cursor.execute(sql_update_massa, tuple(ids_para_desativar))

        # Atualiza o status na tabela principal (resumo)
        sql_update_resumo = f"UPDATE tb_atendimentos SET status = 'DELETADO' WHERE chave_id IN ({format_strings})"
        cursor.execute(sql_update_resumo, tuple(ids_para_desativar))

        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()

def update_atendimentos_no_banco(registros):
    """Atualiza atendimentos existentes no banco de dados."""
    conn = g.db
    if conn is None:
        return 0, "Erro de conexão com o banco de dados."

    cursor = conn.cursor()
    sql_update = """
        UPDATE tb_atendimentos
        SET data = %s, tarefa = %s, responsavel = %s, loja = %s, tipo = %s, acao = %s, assunto = %s
        WHERE chave_id = %s
    """
    try:
        cursor.executemany(sql_update, registros)
        conn.commit()
        return cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        cursor.close()