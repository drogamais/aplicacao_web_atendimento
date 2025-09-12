# aplicacao_web_atendimento/app.py

from flask import Flask, render_template, request, redirect, url_for, flash, g
import uuid
from datetime import date, timedelta
from mysql.connector import Error

# Importando de nossos novos módulos
import database
from config import SECRET_KEY
from constants import (
    TAREFAS_OPCOES, INDEX_RESPONSAVEIS_OPCOES, RESPONSAVEIS_OPCOES,
    TIPOS_OPCOES, ACOES_OPCOES, CONVENIO_TAREFAS_OPCOES, FUNCAO_MAP
)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# --- GESTÃO DA CONEXÃO COM O BANCO DE DADOS ---

@app.before_request
def before_request():
    """
    Abre uma conexão com o banco de dados antes de cada requisição
    e a armazena no contexto da aplicação (g).
    """
    g.db = database.get_db_connection()

@app.teardown_request
def teardown_request(exception):
    """
    Fecha a conexão com o banco de dados ao final de cada requisição,
    se ela existir.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def index():
    today = date.today()
    three_days_ago = today - timedelta(days=3)
    return render_template(
        'index.html',
        tarefas=TAREFAS_OPCOES,
        responsaveis=INDEX_RESPONSAVEIS_OPCOES,
        tipos=TIPOS_OPCOES,
        acoes=ACOES_OPCOES,
        active_page='index',
        #min_date=three_days_ago.isoformat(),
        min_date=None,
        max_date=today.isoformat()
    )

@app.route('/convenio')
def convenio():
    today = date.today()
    three_days_ago = today - timedelta(days=3)
    return render_template(
        'convenio.html',
        tarefas=CONVENIO_TAREFAS_OPCOES,
        responsaveis=["VALERIA APARECIDA BONFIM SOARES"],
        tipos=TIPOS_OPCOES,
        acoes=ACOES_OPCOES,
        active_page='convenio',
        min_date=three_days_ago.isoformat(),
        max_date=today.isoformat()
    )

@app.route('/massa')
def massa_dados():
    today = date.today()
    three_days_ago = today - timedelta(days=3)
    lojas_ativas = database.get_lojas_ativas()
    return render_template(
        'massa.html',
        tarefas=TAREFAS_OPCOES,
        responsaveis=RESPONSAVEIS_OPCOES,
        tipos=TIPOS_OPCOES,
        acoes=ACOES_OPCOES,
        lojas=lojas_ativas,
        active_page='massa',
        min_date=three_days_ago.isoformat(),
        max_date=today.isoformat()
    )

@app.route('/editar')
def editar_dados():
    data_filtro = request.args.get('data_filtro')
    responsavel_filtro = request.args.get('responsavel')

    sql_query = "SELECT * FROM tb_atendimentos WHERE 1=1"
    params = []

    if data_filtro:
        sql_query += " AND data = %s"
        params.append(data_filtro)
    else:
        tres_dias_atras = date.today() - timedelta(days=3)
        sql_query += " AND data >= %s"
        params.append(tres_dias_atras)

    if responsavel_filtro:
        sql_query += " AND responsavel = %s"
        params.append(responsavel_filtro)
    
    sql_query += " ORDER BY data DESC, chave_id DESC"
    
    atendimentos = database.get_atendimentos_para_editar(sql_query, params)
    data_corte = date.today() - timedelta(days=14)

    return render_template(
        'editar.html', 
        atendimentos=atendimentos,
        data_corte=data_corte,
        tarefas_opcoes=TAREFAS_OPCOES,
        responsaveis_opcoes=RESPONSAVEIS_OPCOES,
        tipos_opcoes=TIPOS_OPCOES,
        acoes_opcoes=ACOES_OPCOES,
        active_page='editar',
        filtros={'data_filtro': data_filtro, 'responsavel': responsavel_filtro}
    )

@app.route('/salvar', methods=['POST'])
def salvar_dados():
    data_str = request.form.get('data')
    nome_responsavel = request.form.get('responsavel')
    
    if not data_str or not nome_responsavel:
        flash('Os campos "Data" e "Responsável" são obrigatórios.', 'danger')
        return redirect(request.referrer)

    # Validação da data
    try:
        data_selecionada = date.fromisoformat(data_str)
        today = date.today()
        three_days_ago = today - timedelta(days=3)
        if not (three_days_ago <= data_selecionada <= today):
            flash('A data de lançamento deve estar entre hoje e, no máximo, 3 dias atrás.', 'danger')
            return redirect(request.referrer)
    except ValueError:
        flash('Formato de data inválido.', 'danger')
        return redirect(request.referrer)

    tarefas = request.form.getlist('tarefa')
    lojas = request.form.getlist('loja')
    tipos = request.form.getlist('tipo')
    acoes = request.form.getlist('acao')
    assuntos = request.form.getlist('assunto')

    registros_para_inserir = []
    for i in range(len(lojas)):
        if lojas[i]: 
            if not tarefas[i] or not tipos[i] or not acoes[i]:
                flash(f'Erro na Linha {i+1}: Campos obrigatórios não preenchidos.', 'danger')
                return redirect(request.referrer)
            
            registros_para_inserir.append((
                str(uuid.uuid4()), data_str, tarefas[i], nome_responsavel, FUNCAO_MAP.get(nome_responsavel),
                int(lojas[i]), tipos[i], acoes[i], assuntos[i] or None
            ))

    if not registros_para_inserir:
        flash('Nenhuma linha preenchida para salvar.', 'warning')
        return redirect(request.referrer)

    rowcount, error = database.save_new_atendimentos(registros_para_inserir)
    if error:
        flash(f'Erro ao salvar os dados no banco: {error}', 'danger')
    else:
        flash(f'{rowcount} registros salvos com sucesso!', 'success')

    return redirect(request.referrer)


# aplicacao_web_atendimento/app.py

@app.route('/salvar_massa', methods=['POST'])
def salvar_dados_massa():
    data = request.form.get('data')
    tarefa = request.form.get('tarefa')
    nome_responsavel = request.form.get('responsavel')
    tipo = request.form.get('tipo')
    acao = request.form.get('acao')
    assunto = request.form.get('assunto')
    lojas_selecionadas = request.form.getlist('lojas')

    if not all([data, tarefa, nome_responsavel, tipo, acao]) or not lojas_selecionadas:
        flash('Todos os campos e pelo menos uma loja devem ser preenchidos.', 'danger')
        return redirect(url_for('massa_dados'))

    # Validação da data (se você removeu, pode remover este bloco)
    try:
        data_selecionada = date.fromisoformat(data)
        if data_selecionada > date.today():
            flash('A data de lançamento não pode ser no futuro.', 'danger')
            return redirect(url_for('massa_dados'))
    except (ValueError, TypeError):
        flash('Formato de data inválido.', 'danger')
        return redirect(url_for('massa_dados'))
        
    # --- Nova Lógica de Inserção ---

    # 1. Prepara os registros individuais para a tabela tb_atendimentos_massa
    registros_para_massa = [
        (str(uuid.uuid4()), data, tarefa, nome_responsavel, FUNCAO_MAP.get(nome_responsavel),
         int(loja_num), tipo, acao, assunto or None)
        for loja_num in lojas_selecionadas
    ]

    # 2. Prepara o registro de resumo para a tabela tb_atendimentos
    registro_sumario = [(
        str(uuid.uuid4()), data, tarefa, nome_responsavel, FUNCAO_MAP.get(nome_responsavel),
        -1,  # Loja -1 para indicar inserção em massa
        tipo, acao, assunto or None
    )]

    # 3. Executa as inserções como uma transação
    conn = g.db
    if conn is None:
        flash('Erro de conexão com o banco de dados.', 'danger')
        return redirect(url_for('massa_dados'))

    cursor = None
    try:
        cursor = conn.cursor()
        
        # Insere na nova tabela de massa
        rowcount_massa = database.insert_atendimentos_massa(cursor, registros_para_massa)
        
        # Insere o resumo na tabela principal
        database.insert_atendimentos(cursor, registro_sumario)

        # Se tudo correu bem, comita a transação
        conn.commit()

        flash(f'{rowcount_massa} registros salvos com sucesso na inserção em massa!', 'success')

    except Error as e:
        if conn:
            conn.rollback() # Reverte todas as alterações em caso de erro
        flash(f'Erro ao salvar os dados no banco: {e}', 'danger')
    finally:
        if cursor:
            cursor.close()

    return redirect(url_for('massa_dados'))


@app.route('/atualizar', methods=['POST'])
def atualizar_dados():
    selecionados = request.form.getlist('selecionado')
    if not selecionados:
        flash('Nenhum registro foi selecionado para atualização.', 'warning')
        return redirect(url_for('editar_dados'))
    
    registros_para_atualizar = []
    for chave_id in selecionados:
        registros_para_atualizar.append((
            request.form.get(f'data_{chave_id}'), request.form.get(f'tarefa_{chave_id}'),
            request.form.get(f'responsavel_{chave_id}'), int(request.form.get(f'loja_{chave_id}')), 
            request.form.get(f'tipo_{chave_id}'), request.form.get(f'acao_{chave_id}'),
            request.form.get(f'assunto_{chave_id}') or None, 
            chave_id
        ))
    
    if registros_para_atualizar:
        rowcount, error = database.update_atendimentos_no_banco(registros_para_atualizar)
        if error:
            flash(f'Erro ao atualizar os dados: {error}', 'danger')
        else:
            flash(f'{rowcount} registros atualizados com sucesso!', 'success')
    else:
        flash('Nenhum registro foi modificado.', 'info')
        
    return redirect(url_for('editar_dados'))