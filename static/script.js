document.addEventListener('DOMContentLoaded', function() {
    // --- 1. SELEÇÃO DOS ELEMENTOS ---
    // Encontra o formulário correto na página, seja o padrão ou o de massa
    const form = document.getElementById('atendimento-form') || document.getElementById('atendimento-massa-form');
    const btnLimpar = document.getElementById('btn-limpar');
    
    // Se não houver um formulário ou botão de limpar, o script não precisa continuar.
    if (!form || !btnLimpar) {
        return;
    }

    const allInputs = form.querySelectorAll('input, select');
    const STORAGE_KEY = 'atendimentoFormData';

    // Elementos do Modal e Notificação
    const confirmModal = document.getElementById('confirm-modal');
    const modalBtnConfirm = document.getElementById('modal-btn-confirm');
    const modalBtnCancel = document.getElementById('modal-btn-cancel');
    
    // --- 2. FUNÇÕES AUXILIARES ---
    
    // Mostra uma notificação no canto da tela
    function showNotification(message) {
        const notification = document.getElementById('notification');
        if (notification) {
            notification.textContent = message;
            notification.classList.add('show');
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }
    }

    // Cria uma chave única para cada campo do formulário (para salvar no cache)
    function getUniqueKey(input) {
        const row = input.closest('tr');
        if (row) {
            const rowIndex = Array.from(row.parentElement.children).indexOf(row);
            return `${input.name}_${rowIndex}`;
        }
        return input.id || input.name;
    }

    // Salva os dados do formulário no cache do navegador
    function salvarDadosNoCache() {
        const data = {};
        allInputs.forEach(input => {
            if (input.name || input.id) {
                data[getUniqueKey(input)] = input.value;
            }
        });
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    }

    // Carrega os dados do cache quando a página é aberta
    function carregarDadosDoCache() {
        const savedData = localStorage.getItem(STORAGE_KEY);
        if (savedData) {
            const data = JSON.parse(savedData);
            allInputs.forEach(input => {
                const key = getUniqueKey(input);
                if (data[key] !== undefined) {
                    input.value = data[key];
                }
            });
        }
    }

    // --- 3. EVENTOS ---

    // Carrega dados salvos assim que a página é carregada
    carregarDadosDoCache();

    // Salva os dados sempre que o usuário altera um campo
    form.addEventListener('input', salvarDadosNoCache);
    
    // Limpa o cache quando o formulário é enviado
    form.addEventListener('submit', function() {
        localStorage.removeItem(STORAGE_KEY);
    });

    // Lógica do botão Limpar e Modal de confirmação
    btnLimpar.addEventListener('click', () => confirmModal.classList.add('show-modal'));
    modalBtnCancel.addEventListener('click', () => confirmModal.classList.remove('show-modal'));

    modalBtnConfirm.addEventListener('click', function() {
        // Remove os dados salvos no cache
        localStorage.removeItem(STORAGE_KEY);
        
        // Reseta todos os campos do formulário
        form.reset(); 
        
        // CORREÇÃO: Limpa os campos de Data e Responsável que estão fora da tabela,
        // usando os IDs corretos.
        const dataInput = document.getElementById('data');
        const responsavelInput = document.getElementById('responsavel');
        if(dataInput) dataInput.value = '';
        if(responsavelInput) responsavelInput.value = '';

        // Na página de massa, desmarca todas as lojas
        const checkboxes = document.querySelectorAll('.lojas-checklist input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
        const selecionarTodas = document.getElementById('selecionar-todas');
        if (selecionarTodas) selecionarTodas.checked = false;

        // Esconde o modal
        confirmModal.classList.remove('show-modal');
        
        // Mostra a notificação
        showNotification('Formulário limpo com sucesso!');
    });
});