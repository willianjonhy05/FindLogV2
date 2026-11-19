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
        // 1. Abre o modal de orientações imediatamente (exceto quando retorna com erros de validação)
        abrirModalOrientacao();

        // 2. Pré-visualização imediata da foto capturada pela câmera ou selecionada
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

    // Fallback: garante abertura caso o bundle do Bootstrap termine de carregar no window.onload
    window.addEventListener("load", function () {
        const modalAlertaEl = document.getElementById("modalOrientacaoCadastroItem");
        if (modalAlertaEl && !modalAlertaEl.classList.contains("show")) {
            abrirModalOrientacao();
        }
    });
})();