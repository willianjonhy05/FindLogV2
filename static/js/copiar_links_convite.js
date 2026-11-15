document.addEventListener("DOMContentLoaded", function () {
    const origem = window.location.origin;

    // Preenche a URL completa (ex: https://findlog.com.br/instituicoes/convite/...) nos inputs
    document.querySelectorAll("input[data-path]").forEach(function (input) {
        input.value = origem + input.getAttribute("data-path");
    });

    // Copia para a área de transferência com feedback visual no botão
    document.querySelectorAll(".btn-copiar-link").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const targetId = this.getAttribute("data-target");
            const input = document.getElementById(targetId);
            if (!input) return;

            input.select();
            input.setSelectionRange(0, 99999);

            navigator.clipboard.writeText(input.value).then(() => {
                const htmlOriginal = this.innerHTML;
                this.innerHTML = '<i class="bi bi-check-lg me-1"></i> Copiado!';
                this.classList.remove("btn-primary-custom");
                this.classList.add("btn-success");

                setTimeout(() => {
                    this.innerHTML = htmlOriginal;
                    this.classList.remove("btn-success");
                    this.classList.add("btn-primary-custom");
                }, 2000);
            });
        });
    });
});