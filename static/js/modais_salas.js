document.addEventListener("DOMContentLoaded", function () {
    // 1. Modal de Ativar / Desativar Sala
    const modalStatusEl = document.getElementById("modalStatusSala");
    if (modalStatusEl) {
        modalStatusEl.addEventListener("show.bs.modal", function (event) {
            const botao = event.relatedTarget;
            if (!botao) return;

            const acao = botao.getAttribute("data-action"); // "ativar" ou "desativar"
            const url = botao.getAttribute("data-url");
            const nomeSala = botao.getAttribute("data-sala-nome");
            const localSala = botao.getAttribute("data-sala-local");

            const tituloEl = document.getElementById("modalStatusSalaTitulo");
            const iconeEl = document.getElementById("modalStatusSalaIcon");
            const descEl = document.getElementById("modalStatusSalaDescricao");
            const nomeEl = document.getElementById("modalStatusSalaNome");
            const localEl = document.getElementById("modalStatusSalaLocal");
            const avisoEl = document.getElementById("modalStatusSalaAviso");
            const formEl = document.getElementById("formStatusSala");
            const btnConfirmar = document.getElementById("btnConfirmarStatusSala");

            nomeEl.textContent = nomeSala || "Sala";
            localEl.textContent = localSala || "";
            formEl.setAttribute("action", url);

            if (acao === "ativar") {
                tituloEl.textContent = "Reativar Sala";
                tituloEl.parentElement.className = "modal-title fw-bold d-flex align-items-center gap-2 text-success";
                iconeEl.className = "bi bi-check-circle-fill fs-5 text-success";
                descEl.textContent = "Deseja reativar este ambiente para uso operacional na unidade?";
                avisoEl.innerHTML = '<i class="bi bi-info-circle text-success me-1"></i> A sala voltará a ficar disponível para registro e guarda de itens.';
                btnConfirmar.className = "btn btn-success";
                btnConfirmar.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Sim, reativar';
            } else {
                tituloEl.textContent = "Desativar Sala";
                tituloEl.parentElement.className = "modal-title fw-bold d-flex align-items-center gap-2 text-warning-emphasis";
                iconeEl.className = "bi bi-slash-circle-fill fs-5 text-warning";
                descEl.textContent = "Deseja realmente desativar esta sala temporariamente?";
                avisoEl.innerHTML = '<i class="bi bi-info-circle text-warning-emphasis me-1"></i> O histórico permanece preservado, mas a sala não aparecerá nos formulários de novos itens.';
                btnConfirmar.className = "btn btn-warning text-dark fw-semibold";
                btnConfirmar.innerHTML = '<i class="bi bi-slash-circle me-1"></i> Sim, desativar';
            }
        });
    }

    // 2. Modal de Exclusão Permanente de Sala
    const modalExcluirEl = document.getElementById("modalExcluirSala");
    if (modalExcluirEl) {
        modalExcluirEl.addEventListener("show.bs.modal", function (event) {
            const botao = event.relatedTarget;
            if (!botao) return;

            const url = botao.getAttribute("data-url");
            const nomeSala = botao.getAttribute("data-sala-nome");
            const localSala = botao.getAttribute("data-sala-local");

            document.getElementById("modalExcluirSalaNome").textContent = nomeSala || "Sala";
            document.getElementById("modalExcluirSalaLocal").textContent = localSala || "";
            document.getElementById("formExcluirSala").setAttribute("action", url);
        });
    }
});