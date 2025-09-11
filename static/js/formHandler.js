window.App = window.App || {};

App.formHandler = {
    init: function() {
        const form = document.getElementById('atendimento-form') || document.getElementById('atendimento-massa-form');
        const btnLimpar = document.getElementById('btn-limpar');
        const confirmModal = document.getElementById('confirm-modal');
        
        if (form && btnLimpar && confirmModal) {
            const modalBtnConfirm = document.getElementById('modal-btn-confirm');
            const modalBtnCancel = document.getElementById('modal-btn-cancel');

            btnLimpar.addEventListener('click', () => confirmModal.classList.add('show-modal'));
            modalBtnCancel.addEventListener('click', () => confirmModal.classList.remove('show-modal'));

            modalBtnConfirm.addEventListener('click', function() {
                form.reset();
                
                const dataInput = document.getElementById('data');
                const responsavelInput = document.getElementById('responsavel');
                if(dataInput) dataInput.value = '';
                if(responsavelInput) responsavelInput.value = '';

                if (form.id === 'atendimento-massa-form') {
                    const checkboxes = form.querySelectorAll('.lojas-checklist input[type="checkbox"]');
                    checkboxes.forEach(cb => cb.checked = false);
                    const selecionarTodas = document.getElementById('selecionar-todas');
                    if (selecionarTodas) selecionarTodas.checked = false;
                }

                confirmModal.classList.remove('show-modal');
                showNotification('Formulário limpo com sucesso!');
            });
        }
    }
};