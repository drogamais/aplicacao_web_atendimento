# aplicacao_web_atendimento/run.py

from waitress import serve
from app import app  # Importa a variável 'app' do nosso arquivo app.py

# Inicia o servidor de produção Waitress para a nossa aplicação Flask
if __name__ == '__main__':
    # Escuta em todas as interfaces de rede na porta 8080 (ou outra de sua escolha)
    serve(app, host='127.0.0.1', port=5000)