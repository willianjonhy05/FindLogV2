document.addEventListener('DOMContentLoaded', function () {
    const campoSenha = document.getElementById('senha');
    const botaoSenha = document.getElementById('toggleSenha');
    const iconeSenha = document.getElementById('iconeSenha');

    botaoSenha.addEventListener('click', function () {
        if (campoSenha.type === 'password') {
            campoSenha.type = 'text';

            iconeSenha.classList.remove('bi-eye');
            iconeSenha.classList.add('bi-eye-slash');

            botaoSenha.setAttribute('aria-label', 'Esconder senha');
        } else {
            campoSenha.type = 'password';

            iconeSenha.classList.remove('bi-eye-slash');
            iconeSenha.classList.add('bi-eye');

            botaoSenha.setAttribute('aria-label', 'Mostrar senha');
        }
    });
});