document.addEventListener('DOMContentLoaded', function() {
    // Encontra o formulário principal
    const form = document.querySelector('#atendimento-massa-form');
    if (!form) return; // Se o formulário não existir na página, não faz nada

    // Pega as listas de tarefas que foram embutidas nos atributos 'data-*' do formulário
    const todasTarefas = JSON.parse(form.dataset.todasTarefas);
    const convenioTarefas = JSON.parse(form.dataset.convenioTarefas);

    // Encontra os dropdowns no HTML
    const responsavelSelect = document.querySelector('select[name="responsavel"]');
    const tarefaSelect = document.querySelector('select[name="tarefa"]');

    // Função que limpa e preenche o dropdown de tarefas
    function atualizarOpcoesTarefa(novasTarefas) {
        const valorAtual = tarefaSelect.value;
        tarefaSelect.innerHTML = '<option value="">Selecione...</option>'; // Limpa tudo

        novasTarefas.forEach(function(tarefa) {
            const option = new Option(tarefa, tarefa); // Cria a nova <option>
            tarefaSelect.add(option); // Adiciona ao <select>
        });
        
        // Se a opção que estava selecionada antes ainda existir na nova lista, seleciona ela de novo
        if (novasTarefas.includes(valorAtual)) {
            tarefaSelect.value = valorAtual;
        }
    }

    // Função que decide qual lista de tarefas usar com base no responsável
    function handleResponsavelChange() {
        if (responsavelSelect.value === 'Valéria') {
            atualizarOpcoesTarefa(convenioTarefas);
        } else {
            atualizarOpcoesTarefa(todasTarefas);
        }
    }

    // Adiciona um "ouvinte" para executar a função sempre que o responsável for alterado
    responsavelSelect.addEventListener('change', handleResponsavelChange);

    // Executa a função uma vez no início para garantir que o estado inicial esteja correto
    handleResponsavelChange();
});