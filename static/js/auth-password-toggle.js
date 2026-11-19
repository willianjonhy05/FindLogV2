document.addEventListener('DOMContentLoaded', () => {
    // Alternância de visibilidade de senhas (autocadastro e páginas internas)
    const toggles = document.querySelectorAll('.auth-password-toggle, .toggle-senha[data-target]');

    toggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const targetId = toggle.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const icon = toggle.querySelector('i');

            if (!input) return;

            const mostrando = input.type === 'password';

            input.type = mostrando ? 'text' : 'password';

            if (icon) {
                icon.classList.toggle('bi-eye', !mostrando);
                icon.classList.toggle('bi-eye-slash', mostrando);
            }

            toggle.setAttribute('aria-label', mostrando ? 'Esconder senha' : 'Mostrar senha');
            toggle.setAttribute('aria-pressed', String(mostrando));
        });
    });
});
