document.addEventListener('DOMContentLoaded', function() {
            // --- 1. DECLARAÇÕES DE CONSTANTES ---
            const form = document.getElementById('atendimento-form');
            const formInputs = form.querySelectorAll('input, select');
            const STORAGE_KEY = 'atendimentoFormData';

            // Constantes do Modal de Confirmação e Notificação
            const confirmModal = document.getElementById('confirm-modal');
            const modalBtnConfirm = document.getElementById('modal-btn-confirm');
            const modalBtnCancel = document.getElementById('modal-btn-cancel');
            const btnLimpar = document.getElementById('btn-limpar');

            // --- 2. FUNÇÕES ---
            // Função da notificação de sucesso
            function showNotification(message) {
                const notification = document.getElementById('notification');
                notification.textContent = message;
                notification.classList.add('show');
                setTimeout(function() {
                    notification.classList.remove('show');
                }, 3000);
            }

            // Função para salvar dados no cache
            function salvarDadosNoCache() {
                const data = {};
                formInputs.forEach((input, index) => {
                    const key = `${input.name}_${Math.floor(index / formInputs.length * 10)}`;
                    data[key] = input.value;
                });
                localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
            }

            // Função para carregar dados do cache
            function carregarDadosDoCache() {
                const savedData = localStorage.getItem(STORAGE_KEY);
                if (savedData) {
                    const data = JSON.parse(savedData);
                    formInputs.forEach((input, index) => {
                        const key = `${input.name}_${Math.floor(index / formInputs.length * 10)}`;
                        if (data[key]) {
                            input.value = data[key];
                        }
                    });
                }
            }

            // --- 3. EVENT LISTENERS (LÓGICA DA PÁGINA) ---
            // Carrega os dados do cache quando a página abre
            carregarDadosDoCache();

            // Salva os dados sempre que um campo é alterado
            form.addEventListener('input', salvarDadosNoCache);

            // Limpa o cache após o envio bem-sucedido dos dados
            form.addEventListener('submit', function() {
                localStorage.removeItem(STORAGE_KEY);
            });

            // Mostra o modal ao clicar no botão "Limpar Formulário"
            btnLimpar.addEventListener('click', function() {
                confirmModal.classList.add('show-modal');
            });

            // Esconde o modal ao clicar em "Cancelar"
            modalBtnCancel.addEventListener('click', function() {
                confirmModal.classList.remove('show-modal');
            });

            // Limpa o formulário e esconde o modal ao clicar em "OK"
            modalBtnConfirm.addEventListener('click', function() {
                localStorage.removeItem(STORAGE_KEY);
                form.reset();
                confirmModal.classList.remove('show-modal');
                showNotification('Formulário limpo com sucesso!');
            });
        });