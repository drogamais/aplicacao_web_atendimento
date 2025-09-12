# aplicacao_web_atendimento/database.py

import mysql.connector
from mysql.connector import Error
from flask import g  # Importa o 'g', o contexto global da requisição
from config import DB_CONFIG

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

def update_atendimentos_no_banco(registros):
    """Atualiza atendimentos usando a conexão da requisição atual (g.db)."""
    conn = g.db
    if conn is None: return 0, "Erro de conexão com o banco de dados."
    
    update_cursor = conn.cursor()
    sql_update = """
        UPDATE tb_atendimentos SET 
            data = %s, tarefa = %s, responsavel = %s, loja = %s, 
            tipo = %s, acao = %s, assunto = %s 
        WHERE chave_id = %s
    """
    try:
        update_cursor.executemany(sql_update, registros)
        conn.commit()
        return update_cursor.rowcount, None
    except Error as e:
        conn.rollback()
        return 0, str(e)
    finally:
        update_cursor.close()

def insert_atendimentos(cursor, registros):
    """Prepara e executa a inserção para a tabela tb_atendimentos."""
    sql_insert = """
        INSERT INTO tb_atendimentos (chave_id, data, tarefa, responsavel, funcao, loja, tipo, acao, assunto)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(sql_insert, registros)
    return cursor.rowcount

def insert_atendimentos_massa(cursor, registros):
    """Prepara e executa a inserção para a tabela tb_atendimentos_massa."""
    sql_insert = """
        INSERT INTO tb_atendimentos_massa (chave_id, data, tarefa, responsavel, funcao, loja, tipo, acao, assunto)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(sql_insert, registros)
    return cursor.rowcount