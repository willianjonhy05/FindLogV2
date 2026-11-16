(function () {
    function abrirModalOrientacao() {
        const modalAlertaEl = document.getElementById("modalOrientacaoCadastroItem");
        const temErrosForm = document.querySelector(".invalid-feedback.d-block") !== null;

        if (!modalAlertaEl || temErrosForm) return;

        if (typeof bootstrap !== "undefined" && bootstrap.Modal) {
            const modalAlerta = bootstrap.Modal.getOrCreateInstance(modalAlertaEl, {
                backdrop: "static",
                keyboard: false,
            });
            modalAlerta.show();
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        // 1. Abre o modal de orientações imediatamente com o fundo escurecido
        abrirModalOrientacao();

        // 2. Ativa busca digitável nos selects de Categoria, Local e Local Guardado (Tom Select)
        if (typeof TomSelect !== "undefined") {
            document.querySelectorAll("select.select-pesquisavel").forEach(function (selectEl) {
                new TomSelect(selectEl, {
                    create: false,
                    allowEmptyOption: true,
                    sortField: {
                        field: "text",
                        direction: "asc",
                    },
                    render: {
                        no_results: function () {
                            return '<div class="no-results p-2 text-muted small">Nenhuma opção encontrada.</div>';
                        },
                    },
                });
            });
        }

        // 3. Pré-visualização imediata da foto capturada pela câmera ou selecionada
        const inputFoto = document.getElementById("id_foto");
        const previewContainer = document.getElementById("previewFotoContainer");
        const previewImg = document.getElementById("previewFotoImg");

        if (inputFoto && previewContainer && previewImg) {
            inputFoto.addEventListener("change", function () {
                const arquivo = this.files && this.files[0];
                if (arquivo) {
                    const reader = new FileReader();
                    reader.onload = function (e) {
                        previewImg.src = e.target.result;
                        previewContainer.classList.remove("d-none");
                    };
                    reader.readAsDataURL(arquivo);
                } else {
                    previewImg.src = "";
                    previewContainer.classList.add("d-none");
                }
            });
        }
    });

    // Fallback: se o script do Bootstrap terminar de carregar no window.onload, garante a abertura
    window.addEventListener("load", function () {
        const modalAlertaEl = document.getElementById("modalOrientacaoCadastroItem");
        if (modalAlertaEl && !modalAlertaEl.classList.contains("show")) {
            abrirModalOrientacao();
        }
    });
})();