document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".btn-copiar-modal").forEach(function (btn) {
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