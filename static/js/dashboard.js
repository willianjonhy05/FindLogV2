/**
 * FindLog - Dashboard Logic
 * Controle de Sidebar responsiva, overlay e interações de teclado/redimensionamento.
 */

document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const overlay = document.getElementById('overlay');
    const sidebarLinks = document.querySelectorAll('.sidebar-nav .nav-item');

    // Abre a sidebar no mobile
    const openSidebar = () => {
        if (!sidebar || !overlay) return;
        sidebar.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden'; // Impede o scroll do body enquanto o menu está aberto
        if (sidebarToggle) {
            sidebarToggle.setAttribute('aria-expanded', 'true');
        }
    };

    // Fecha a sidebar no mobile
    const closeSidebar = () => {
        if (!sidebar || !overlay) return;
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = ''; // Restaura o scroll natural
        if (sidebarToggle) {
            sidebarToggle.setAttribute('aria-expanded', 'false');
        }
    };

    // Alternar estado ao clicar no botão hamburger
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            if (sidebar.classList.contains('active')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    // Fechar ao clicar no overlay escuro
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // Fechar ao pressionar a tecla ESC para maior acessibilidade (a11y)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });

    // Fechar automaticamente ao clicar em um link interno (mobile)
    sidebarLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 992) {
                closeSidebar();
            }
        });
    });

    // Se o usuário redimensionar da tela mobile para desktop com o menu aberto, limpa estados residuais
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 992 && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });
});