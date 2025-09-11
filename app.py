from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
import datetime
import uuid
from datetime import date, timedelta

# --- CONFIGURAÇÃO ---
app = Flask(__name__)
app.secret_key = 'meu-app-e-muito-seguro-12345'

# --- OPÇÕES PARA OS MENUS (HARDCODED) ---
TAREFAS_OPCOES = [
    "ACODE - 2024", "ACODE - 2025", "ACODE - 2026", "ADMINISTRATIVO", 
    "CAMPANHA PBM", "CAMPANHAS", "COMERCIAL", "CONVENIO", "DEVOLUÇÕES", 
    "DÚVIDAS GERAIS", "FACHADA E LAYOUT", "FINANCEIRO", "LOGISTICA", 
    "MATERIAIS DE MARKETING", "MATERIAIS OBRIGATÓRIOS", "PBM", "PEDIDOS", 
    "SOMAR", "SUPORTE OPERACIONAL"
]
RESPONSAVEIS_OPCOES = [
    "LÍVIA VICTORIA LOURENÇO", "NATÁLIA BICHOFF", "DIEGO CORRENTE TANACA", 
    "FABIO HENRIQUE DE PÁDUA", "MIGUEL KENJI IWAMOTO", "LUIZ FELIPHE MARROCO", 
    "VALERIA APARECIDA BONFIM SOARES"
]
TIPOS_OPCOES = ["WHATSAPP", "TELEFONE", "EMAIL"]
ACOES_OPCOES = ["ATIVA", "PASSIVA"] 

# --- MAPEAMENTO DE RESPONSÁVEL PARA FUNÇÃO ---
FUNCAO_MAP = {
    "LÍVIA VICTORIA LOURENÇO": "FOCAL",
    "NATÁLIA BICHOFF": "FOCAL",
    "DIEGO CORRENTE TANACA": "COORDENADOR",
    "FABIO HENRIQUE DE PÁDUA": "AUDITOR",
    "MIGUEL KENJI IWAMOTO": "AUDITOR",
    "LUIZ FELIPHE MARROCO": "AUDITOR",
    "VALERIA APARECIDA BONFIM SOARES": "CONVENIO"
}

# Detalhes da sua conexão com o banco de dados MySQL
db_config = {
    "user": "drogamais",
    "password": "dB$MYSql@2119",
    "host": "10.48.12.20",
    "port": 3306,
    "database": "dbSults",
    "collation": "utf8mb4_general_ci"
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def get_lojas_ativas():
    """Busca no banco de dados todas as lojas com status ATIVO = 1 e número válido."""
    conn = get_db_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("USE drogamais")
        # Query ajustada para filtrar lojas sem número ou com número 0
        query = """
            SELECT LOJA_NUMERO, FANTASIA 
            FROM tb_loja 
            WHERE ATIVO = 1 AND LOJA_NUMERO IS NOT NULL AND LOJA_NUMERO > 0
            ORDER BY LOJA_NUMERO
        """
        cursor.execute(query)
        lojas = cursor.fetchall()
        return lojas
    except Error as e:
        print(f"Erro ao buscar lojas: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def index():
    """ Rota principal que exibe o formulário de grade. """
    return render_template(
        'index.html', 
        tarefas=TAREFAS_OPCOES,
        responsaveis=RESPONSAVEIS_OPCOES,
        tipos=TIPOS_OPCOES,
        acoes=ACOES_OPCOES
    )
    
# ... (As rotas /salvar, /editar, e /atualizar permanecem as mesmas) ...
@app.route('/salvar', methods=['POST'])
def salvar_dados():
    """ Rota que recebe os dados do formulário e salva no banco. """
    datas = request.form.getlist('data')
    tarefas = request.form.getlist('tarefa')
    nomes_responsaveis = request.form.getlist('responsavel')
    lojas = request.form.getlist('loja')
    tipos = request.form.getlist('tipo')
    acoes = request.form.getlist('acao')
    assuntos = request.form.getlist('assunto')

    registros_para_inserir = []
    
    for i in range(len(datas)):
        if datas[i]:
            if not tarefas[i] or not nomes_responsaveis[i] or not lojas[i] or not tipos[i] or not acoes[i]:
                flash(f'Erro na Linha {i+1}: Todos os campos, exceto "Assunto", são obrigatórios.', 'danger')
                return redirect(url_for('index'))
            
            try:
                loja_num = int(lojas[i])
                if not (0 <= loja_num <= 999):
                    flash(f'Erro na Linha {i+1}: O número da loja deve estar entre 1 e 999.', 'danger')
                    return redirect(url_for('index'))
            except ValueError:
                flash(f'Erro na Linha {i+1}: O valor da loja deve ser um número.', 'danger')
                return redirect(url_for('index'))
            
            chave_unica = str(uuid.uuid4())
            responsavel_atual = nomes_responsaveis[i]
            funcao_atual = FUNCAO_MAP.get(responsavel_atual, None)

            novo_registro = (
                chave_unica,
                datas[i],
                tarefas[i],
                responsavel_atual,
                funcao_atual,
                loja_num,
                tipos[i],
                acoes[i],
                assuntos[i] or None
            )
            registros_para_inserir.append(novo_registro)

    if not registros_para_inserir:
        flash('Nenhum dado preenchido para salvar.', 'warning')
        return redirect(url_for('index'))

    conn = get_db_connection()
    if conn is None:
        flash('Erro de conexão com o banco de dados. Verifique as credenciais e a rede.', 'danger')
        return redirect(url_for('index'))
        
    cursor = conn.cursor()
    
    sql_insert = """
        INSERT INTO tb_atendimentos (chave_id, data, tarefa, responsavel, funcao, loja, tipo, acao, assunto)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        cursor.executemany(sql_insert, registros_para_inserir)
        conn.commit()
        flash(f'{cursor.rowcount} registros salvos com sucesso!', 'success')
    except Error as e:
        conn.rollback()
        flash(f'Erro ao salvar os dados no banco: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('index'))


@app.route('/editar')
def editar_dados():
    """ Rota para exibir os dados para edição, agora com filtros. """
    conn = get_db_connection()
    if conn is None:
        return "<h1>Erro: Não foi possível conectar ao banco de dados.</h1>"
    
    cursor = conn.cursor(dictionary=True)

    # --- LÓGICA DE FILTRO ALTERADA ---
    data_filtro = request.args.get('data_filtro') # Pega o novo campo de data única
    responsavel_filtro = request.args.get('responsavel')

    sql_query = "SELECT * FROM tb_atendimentos WHERE 1=1"
    params = []

    # Adiciona filtros à query dinamicamente
    if data_filtro:
        # Se uma data específica foi fornecida, filtra por ela
        sql_query += " AND data = %s"
        params.append(data_filtro)
    else:
        # Se nenhuma data foi fornecida, usa o padrão dos últimos 3 dias
        tres_dias_atras = date.today() - timedelta(days=1)
        sql_query += " AND data >= %s"
        params.append(tres_dias_atras)

    if responsavel_filtro:
        sql_query += " AND responsavel = %s"
        params.append(responsavel_filtro)
    
    sql_query += " ORDER BY data DESC, chave_id DESC"
    
    cursor.execute(sql_query, tuple(params))
    atendimentos = cursor.fetchall()
    
    cursor.close()
    conn.close()

    data_corte = date.today() - timedelta(days=3)

    return render_template(
        'editar.html', 
        atendimentos=atendimentos,
        data_corte=data_corte,
        tarefas_opcoes=TAREFAS_OPCOES,
        responsaveis_opcoes=RESPONSAVEIS_OPCOES,
        tipos_opcoes=TIPOS_OPCOES,
        acoes_opcoes=ACOES_OPCOES,
        # Passa o novo filtro de volta para o template
        filtros={
            'data_filtro': data_filtro,
            'responsavel': responsavel_filtro
        }
    )

@app.route('/atualizar', methods=['POST'])
def atualizar_dados():
    """ Rota que recebe os dados do formulário de edição e atualiza no banco. """
    selecionados = request.form.getlist('selecionado')

    if not selecionados:
        flash('Nenhum registro foi selecionado para atualização.', 'warning')
        return redirect(url_for('editar_dados'))

    conn = get_db_connection()
    if conn is None:
        flash('Erro de conexão com o banco de dados.', 'danger')
        return redirect(url_for('editar_dados'))
    
    cursor = conn.cursor(dictionary=True)
    
    data_corte = date.today() - timedelta(days=3)
    registros_para_atualizar = []
    
    for chave_id in selecionados:
        cursor.execute("SELECT data FROM tb_atendimentos WHERE chave_id = %s", (chave_id,))
        registro_original = cursor.fetchone()
        
        if not registro_original:
            flash(f'Erro: Registro com chave {chave_id} não encontrado.', 'danger')
            continue

        if registro_original['data'] < data_corte:
            flash(f'Atenção: O registro de {registro_original["data"].strftime("%d/%m/%Y")} não pode ser alterado (mais de 3 dias).', 'warning')
            continue

        data = request.form.get(f'data_{chave_id}')
        tarefa = request.form.get(f'tarefa_{chave_id}')
        responsavel = request.form.get(f'responsavel_{chave_id}')
        loja = request.form.get(f'loja_{chave_id}')
        tipo = request.form.get(f'tipo_{chave_id}')
        acao = request.form.get(f'acao_{chave_id}')
        assunto = request.form.get(f'assunto_{chave_id}')

        if not all([data, tarefa, responsavel, loja, tipo, acao]):
             flash(f'Erro na linha com chave {chave_id}: Todos os campos, exceto "Assunto", são obrigatórios.', 'danger')
             continue

        registros_para_atualizar.append((
            data, tarefa, responsavel, int(loja), 
            tipo, acao, assunto or None, 
            chave_id
        ))
    
    if registros_para_atualizar:
        sql_update = """
            UPDATE tb_atendimentos SET 
                data = %s, tarefa = %s, responsavel = %s, loja = %s, 
                tipo = %s, acao = %s, assunto = %s 
            WHERE chave_id = %s
        """
        try:
            update_cursor = conn.cursor()
            update_cursor.executemany(sql_update, registros_para_atualizar)
            conn.commit()
            flash(f'{update_cursor.rowcount} registros atualizados com sucesso!', 'success')
        except Error as e:
            conn.rollback()
            flash(f'Erro ao atualizar os dados: {e}', 'danger')
        finally:
            if 'update_cursor' in locals() and update_cursor:
                update_cursor.close()
    else:
        flash('Nenhum registro foi modificado ou era válido para atualização.', 'info')

    cursor.close()
    conn.close()

    return redirect(url_for('editar_dados'))

@app.route('/massa')
def massa_dados():
    """ Rota que exibe o formulário de grade para inserção em massa. """
    lojas_ativas = get_lojas_ativas()
    return render_template(
        'massa.html', 
        tarefas=TAREFAS_OPCOES,
        responsaveis=RESPONSAVEIS_OPCOES,
        tipos=TIPOS_OPCOES,
        acoes=ACOES_OPCOES,
        lojas=lojas_ativas  # Passa a lista de lojas para o template
    )

@app.route('/salvar_massa', methods=['POST'])
def salvar_dados_massa():
    """ Rota que recebe os dados do formulário em massa e salva no banco. """
    data = request.form.get('data')
    tarefa = request.form.get('tarefa')
    nome_responsavel = request.form.get('responsavel')
    tipo = request.form.get('tipo')
    acao = request.form.get('acao')
    assunto = request.form.get('assunto')
    lojas_selecionadas = request.form.getlist('lojas')

    if not all([data, tarefa, nome_responsavel, tipo, acao]):
        flash('Todos os campos, exceto "Assunto" e a seleção de lojas, são obrigatórios.', 'danger')
        return redirect(url_for('massa_dados'))
        
    if not lojas_selecionadas:
        flash('Nenhuma loja foi selecionada.', 'danger')
        return redirect(url_for('massa_dados'))

    registros_para_inserir = []
    
    for loja_num_str in lojas_selecionadas:
        loja_num = int(loja_num_str)
        
        chave_unica = str(uuid.uuid4())
        funcao_atual = FUNCAO_MAP.get(nome_responsavel, None)

        novo_registro = (
            chave_unica, data, tarefa, nome_responsavel, funcao_atual,
            loja_num, tipo, acao, assunto or None
        )
        registros_para_inserir.append(novo_registro)

    if not registros_para_inserir:
        flash('Nenhum dado válido para salvar.', 'danger')
        return redirect(url_for('massa_dados'))

    conn = get_db_connection()
    if conn is None:
        flash('Erro de conexão com o banco de dados.', 'danger')
        return redirect(url_for('massa_dados'))
        
    cursor = conn.cursor()
    
    sql_insert = """
        INSERT INTO tb_atendimentos (chave_id, data, tarefa, responsavel, funcao, loja, tipo, acao, assunto)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        cursor.executemany(sql_insert, registros_para_inserir)
        conn.commit()
        flash(f'{cursor.rowcount} registros salvos com sucesso!', 'success')
    except Error as e:
        conn.rollback()
        flash(f'Erro ao salvar os dados no banco: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('massa_dados'))


if __name__ == '__main__':
    app.run(debug=True)