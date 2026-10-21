/**
 * FindLog - Confirmação de Exclusão com Modal Bootstrap 5
 * Suporta tanto exclusão via Link (GET) quanto via Formulário (POST).
 */

document.addEventListener('DOMContentLoaded', () => {
    const modalElement = document.getElementById('modalConfirmarExclusao');
    if (!modalElement) return;

    const modalInstance = new bootstrap.Modal(modalElement);
    const modalItemNome = document.getElementById('modalItemNome');
    const modalBtnConfirmar = document.getElementById('modalBtnConfirmar');

    // Variáveis de controle de ação
    let formularioAlvo = null;
    let urlDestino = null;

    // Escuta cliques em qualquer botão de exclusão
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', (event) => {
            event.preventDefault();

            // Reseta controles
            formularioAlvo = null;
            urlDestino = null;

            // Identifica se o botão faz parte de um <form> (caso das mensagens)
            const parentForm = button.closest('form');
            if (parentForm) {
                formularioAlvo = parentForm;
            } else {
                // Caso seja um link <a> (como instituições)
                urlDestino = button.getAttribute('href');
            }

            const nomeItem = button.getAttribute('data-nome') || 'este registro';

            // Atualiza os dados no modal
            if (modalItemNome) {
                modalItemNome.textContent = nomeItem;
            }

            // Exibe o modal
            modalInstance.show();
        });
    });

    // Quando o usuário confirma a exclusão no Modal
    if (modalBtnConfirmar) {
        modalBtnConfirmar.addEventListener('click', () => {
            if (formularioAlvo) {
                // Submete o formulário via POST de forma limpa e segura
                formularioAlvo.submit();
            } else if (urlDestino) {
                // Redireciona via GET
                window.location.href = urlDestino;
            }
        });
    }
});