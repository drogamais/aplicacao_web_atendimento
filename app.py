# aplicacao_web_atendimento/app.py

from flask import Flask, render_template, request, redirect, url_for, flash, g, session
import uuid
from datetime import date, timedelta
from mysql.connector import Error

# Importando de nossos novos módulos
import database
from config import SECRET_KEY
from constants import (
    TAREFAS_OPCOES, INDEX_RESPONSAVEIS_OPCOES, RESPONSAVEIS_OPCOES,
    TIPOS_OPCOES, ACOES_OPCOES, CONVENIO_TAREFAS_OPCOES, FUNCAO_MAP,
    DATE_FILTER_ENABLED  # Importamos a nossa nova "chave"
)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# --- GESTÃO DA CONEXÃO COM O BANCO DE DADOS ---

@app.before_request
def before_request():
    g.db = database.get_db_connection()

@app.teardown_request
def teardown_request(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- FUNÇÃO AUXILIAR DE VALIDAÇÃO DE DATA ---

def get_date_rules():
    """Retorna as datas mínima e máxima com base na feature flag."""
    today = date.today()
    min_date_obj = None
    if DATE_FILTER_ENABLED:
        min_date_obj = today - timedelta(days=3)
    return min_date_obj, today

def is_valid_date(date_str):
    """Verifica se a data está dentro do intervalo permitido pela feature flag."""
    if not date_str:
        return False, "O campo 'Data' é obrigatório."
    
    try:
        selected_date = date.fromisoformat(date_str)
        min_date, max_date = get_date_rules()

        if selected_date > max_date:
            return False, "A data de lançamento não pode ser no futuro."
        
        if DATE_FILTER_ENABLED and selected_date < min_date:
            return False, f"A data não pode ser anterior a {min_date.strftime('%d/%m/%Y')}."

        return True, None
    except (ValueError, TypeError):
        return False, "Formato de data inválido."

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def index():
    # ALTERAÇÃO 2: Lógica para limpar o formulário
    if 'limpar' in request.args:
        session.pop('form_data', None)
        # Redireciona para remover o parâmetro ?limpar=1 da URL
        return redirect(url_for('index'))

    min_date, max_date = get_date_rules()
    data_selecionada = request.args.get('data')
    responsavel_selecionado = request.args.get('responsavel')

    # ALTERAÇÃO 3: Pega os dados da sessão e prepara as linhas para o template
    form_data = session.get('form_data', {})
    linhas_formulario = []
    
    # Se houver dados na sessão, recria as linhas preenchidas
    if form_data:
        num_linhas_preenchidas = len(form_data.get('lojas', []))
        for i in range(num_linhas_preenchidas):
            # Adiciona apenas as linhas que foram de fato preenchidas (tinham loja)
            if form_data['lojas'][i]:
                linhas_formulario.append({
                    'tarefa': form_data['tarefas'][i],
                    'loja': form_data['lojas'][i],
                    'tipo': form_data['tipos'][i],
                    'acao': form_data['acoes'][i],
                    'assunto': form_data['assuntos'][i]
                })

    # Completa com linhas vazias até atingir o total de 7
    num_linhas_vazias = 7 - len(linhas_formulario)
    for _ in range(num_linhas_vazias):
        linhas_formulario.append({})

    return render_template(
        'index.html',
        tarefas=TAREFAS_OPCOES,
        responsaveis=INDEX_RESPONSAVEIS_OPCOES,
        tipos=TIPOS_OPCOES,
        acoes=ACOES_OPCOES,
        active_page='index',
        min_date=min_date.isoformat() if min_date else None,
        max_date=max_date.isoformat(),
        data_selecionada=data_selecionada,
        responsavel_selecionado=responsavel_selecionado,
        linhas_formulario=linhas_formulario # Envia as linhas processadas
    )

@app.route('/convenio')
def convenio():
    # ALTERAÇÃO 4: Lógica similar para a página de convênio
    if 'limpar' in request.args:
        session.pop('form_data', None)
        return redirect(url_for('convenio'))
        
    min_date, max_date = get_date_rules()
    data_selecionada = request.args.get('data')
    
    form_data = session.get('form_data', {})
    linhas_formulario = []
    if form_data:
        num_linhas_preenchidas = len(form_data.get('lojas', []))
        for i in range(num_linhas_preenchidas):
            if form_data['lojas'][i]:
                linhas_formulario.append({
                    'tarefa': form_data['tarefas'][i],
                    'loja': form_data['lojas'][i],
                    'tipo': form_data['tipos'][i],
                    'acao': form_data['acoes'][i],
                    'assunto': form_data['assuntos'][i]
                })
    
    num_linhas_vazias = 7 - len(linhas_formulario)
    for _ in range(num_linhas_vazias):
        linhas_formulario.append({})

    return render_template(
        'convenio.html',
        tarefas=CONVENIO_TAREFAS_OPCOES,
        responsaveis=["VALERIA APARECIDA BONFIM SOARES"],
        tipos=TIPOS_OPCOES,
        acoes=ACOES_OPCOES,
        active_page='convenio',
        min_date=min_date.isoformat() if min_date else None,
        max_date=max_date.isoformat(),
        data_selecionada=data_selecionada,
        # O responsável é fixo, mas a lógica de reter a data é útil
        responsavel_selecionado="VALERIA APARECIDA BONFIM SOARES",
        linhas_formulario=linhas_formulario
    )

@app.route('/massa')
def massa_dados():
    # ALTERAÇÃO 1: Lógica para limpar o formulário em massa
    if 'limpar' in request.args:
        session.pop('massa_form_data', None)
        return redirect(url_for('massa_dados'))

    min_date, max_date = get_date_rules()
    lojas_ativas = database.get_lojas_ativas()
    
    # ALTERAÇÃO 2: Pega os dados da sessão para repopular o formulário
    # Usamos uma chave diferente para não conflitar com o outro formulário
    form_data = session.get('massa_form_data', {})

    return render_template(
        'massa.html',
        tarefas=TAREFAS_OPCOES,
        responsaveis=RESPONSAVEIS_OPCOES,
        tipos=TIPOS_OPCOES,
        acoes=ACOES_OPCOES,
        lojas=lojas_ativas,
        active_page='massa',
        min_date=min_date.isoformat() if min_date else None,
        max_date=max_date.isoformat(),
        form_data=form_data # Envia os dados da sessão para o template
    )


@app.route('/editar')
def editar_dados():
    data_filtro = request.args.get('data_filtro')
    responsavel_filtro = request.args.get('responsavel')

    # Query base para atendimentos normais (não inclui resumos de massa)
    query_normal = "SELECT chave_id, data, tarefa, responsavel, loja, tipo, acao, assunto, 'normal' as origem FROM tb_atendimentos WHERE loja <> -1"
    
    # Query base para atendimentos em massa
    query_massa = "SELECT chave_id, data, tarefa, responsavel, loja, tipo, acao, assunto, 'massa' as origem FROM tb_atendimentos_massa WHERE 1=1"

    params = []
    where_clauses = ""

    if data_filtro:
        # Se o usuário está filtrando por uma data, usamos a data que ele escolheu.
        where_clauses += " AND data = %s"
        params.append(data_filtro)
    else:
        # Se o usuário ACABOU de entrar na página (sem filtro de data),
        # aplicamos o padrão de mostrar apenas os últimos 3 dias.
        tres_dias_atras = date.today() - timedelta(days=3)
        where_clauses += " AND data >= %s"
        params.append(tres_dias_atras)

    if responsavel_filtro:
        where_clauses += " AND responsavel = %s"
        params.append(responsavel_filtro)

    # Finaliza as strings das queries
    sql_query_normal = query_normal + where_clauses
    sql_query_massa = query_massa + where_clauses
    
    # Executa cada consulta separadamente
    atendimentos_normal = database.get_atendimentos_para_editar(sql_query_normal, params)
    atendimentos_massa = database.get_atendimentos_para_editar(sql_query_massa, params)
    
    # Combina as duas listas de resultados
    todos_atendimentos = atendimentos_normal + atendimentos_massa
    
    # Ordena a lista combinada pela data, do mais recente para o mais antigo
    if todos_atendimentos:
        todos_atendimentos.sort(key=lambda x: x['data'], reverse=True)

    data_corte = date.today() - timedelta(days=14)

    return render_template(
        'editar.html', 
        atendimentos=todos_atendimentos,
        data_corte=data_corte,
        tarefas_opcoes=TAREFAS_OPCOES,
        responsaveis_opcoes=RESPONSAVEIS_OPCOES,
        tipos_opcoes=TIPOS_OPCOES,
        acoes_opcoes=ACOES_OPCOES,
        active_page='editar',
        filtros={'data_filtro': data_filtro, 'responsavel': responsavel_filtro}
    )

@app.route('/deletar_massa')
def deletar_massa():
    """
    Nova rota para a página de exclusão de registros em massa.
    Busca apenas os registros "resumo" (loja = -1).
    """
    atendimentos_massa = database.get_atendimentos_massa_para_deletar()
    return render_template(
        'deletar_massa.html',
        atendimentos=atendimentos_massa,
        active_page='deletar_massa'
    )

@app.route('/salvar', methods=['POST'])
def salvar_dados():
    data_str = request.form.get('data')
    nome_responsavel = request.form.get('responsavel')
    origin_page = request.form.get('origin_page', 'index')

    # Validações...
    if not nome_responsavel:
        flash('O campo "Responsável" é obrigatório.', 'danger')
        return redirect(url_for(origin_page, data=data_str, responsavel=nome_responsavel))

    is_valid, error_msg = is_valid_date(data_str)
    if not is_valid:
        flash(error_msg, 'danger')
        return redirect(url_for(origin_page, data=data_str, responsavel=nome_responsavel))

    # Pega os dados das listas
    tarefas = request.form.getlist('tarefa')
    lojas = request.form.getlist('loja')
    tipos = request.form.getlist('tipo')
    acoes = request.form.getlist('acao')
    assuntos = request.form.getlist('assunto')

    # ALTERAÇÃO 5: Guarda os dados do formulário na sessão
    session['form_data'] = {
        'tarefas': tarefas,
        'lojas': lojas,
        'tipos': tipos,
        'acoes': acoes,
        'assuntos': assuntos
    }

    registros_para_inserir = []
    for i in range(len(lojas)):
        if lojas[i]: 
            if not tarefas[i] or not tipos[i] or not acoes[i]:
                flash(f'Erro na Linha {i+1}: Campos obrigatórios não preenchidos.', 'danger')
                return redirect(url_for(origin_page, data=data_str, responsavel=nome_responsavel))
            
            registros_para_inserir.append((
                str(uuid.uuid4()), data_str, tarefas[i], nome_responsavel, FUNCAO_MAP.get(nome_responsavel),
                int(lojas[i]), tipos[i], acoes[i], assuntos[i] or None
            ))

    if not registros_para_inserir:
        flash('Nenhuma linha preenchida para salvar.', 'warning')
        return redirect(url_for(origin_page, data=data_str, responsavel=nome_responsavel))

    rowcount, error = database.save_new_atendimentos(registros_para_inserir)
    if error:
        flash(f'Erro ao salvar os dados no banco: {error}', 'danger')
    else:
        # Após salvar com sucesso, limpa os dados da sessão para a próxima inserção ser limpa.
        session.pop('form_data', None)
        flash(f'{rowcount} registros salvos com sucesso!', 'success')

    # Redireciona mantendo apenas data e responsável
    return redirect(url_for(origin_page, data=data_str, responsavel=nome_responsavel))


@app.route('/salvar_massa', methods=['POST'])
def salvar_dados_massa():
    # Pega os dados do formulário
    data_str = request.form.get('data')
    tarefa = request.form.get('tarefa')
    nome_responsavel = request.form.get('responsavel')
    tipo = request.form.get('tipo')
    acao = request.form.get('acao')
    assunto = request.form.get('assunto')
    lojas_selecionadas = request.form.getlist('lojas')

    # ALTERAÇÃO 3: Guarda os dados do formulário na sessão ANTES das validações
    session['massa_form_data'] = {
        'data': data_str,
        'tarefa': tarefa,
        'responsavel': nome_responsavel,
        'tipo': tipo,
        'acao': acao,
        'assunto': assunto,
        'lojas_selecionadas': lojas_selecionadas
    }

    # Validações
    is_valid, error_msg = is_valid_date(data_str)
    if not is_valid:
        flash(error_msg, 'danger')
        return redirect(url_for('massa_dados'))

    if not all([tarefa, nome_responsavel, tipo, acao]) or not lojas_selecionadas:
        flash('Todos os campos (exceto Assunto) e pelo menos uma loja devem ser preenchidos.', 'danger')
        return redirect(url_for('massa_dados'))

    # ... (lógica para criar os registros para o banco de dados) ...
    # O código abaixo permanece o mesmo
    id_massa = str(uuid.uuid4())
    registros_para_massa = [
        (str(uuid.uuid4()), id_massa, data_str, tarefa, nome_responsavel, FUNCAO_MAP.get(nome_responsavel),
         int(loja_num), tipo, acao, assunto or None)
        for loja_num in lojas_selecionadas
    ]
    registro_sumario = [(
        id_massa, data_str, tarefa, nome_responsavel, FUNCAO_MAP.get(nome_responsavel),
        -1, tipo, acao, assunto or None
    )]

    conn = g.db
    # ... (lógica de inserção no banco de dados) ...
    
    cursor = None
    try:
        cursor = conn.cursor()
        database.insert_atendimentos(cursor, registro_sumario)
        rowcount_massa = database.insert_atendimentos_massa(cursor, registros_para_massa)
        conn.commit()
        
        # ALTERAÇÃO 4: Se tudo deu certo, limpa os dados da sessão
        session.pop('massa_form_data', None)
        flash(f'{rowcount_massa} registros salvos com sucesso na inserção em massa!', 'success')

    except Error as e:
        if conn:
            conn.rollback()
        flash(f'Erro ao salvar os dados no banco: {e}', 'danger')
        # Se deu erro, os dados continuam na sessão e o formulário será repopulado
        return redirect(url_for('massa_dados'))
    finally:
        if cursor:
            cursor.close()

    # Se deu sucesso, redireciona sem os dados do formulário, mantendo apenas a data e o responsável como antes
    return redirect(url_for('massa_dados', data=data_str, responsavel=nome_responsavel))


@app.route('/executar_delecao_massa', methods=['POST'])
def executar_delecao_massa():
    """
    Nova rota para processar a exclusão dos registros em massa selecionados.
    """
    ids_para_deletar = request.form.getlist('selecionado')
    if not ids_para_deletar:
        flash('Nenhum registro foi selecionado para exclusão.', 'warning')
        return redirect(url_for('deletar_massa'))

    rowcount, error = database.delete_atendimentos_massa(ids_para_deletar)
    if error:
        flash(f'Erro ao deletar os registros: {error}', 'danger')
    else:
        flash(f'{rowcount} registros em massa foram deletados com sucesso!', 'success')
    
    return redirect(url_for('deletar_massa'))


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