document.addEventListener("DOMContentLoaded", function () {
    const modalStatusEl = document.getElementById("modalStatusUsuario");
    if (!modalStatusEl) return;

    modalStatusEl.addEventListener("show.bs.modal", function (event) {
        const botao = event.relatedTarget;
        if (!botao) return;

        const acao = botao.getAttribute("data-action"); // "ativar" ou "desativar"
        const url = botao.getAttribute("data-url");
        const nomeUsuario = botao.getAttribute("data-usuario-nome");
        const infoUsuario = botao.getAttribute("data-usuario-info");

        const tituloEl = document.getElementById("modalStatusUsuarioTitulo");
        const iconeEl = document.getElementById("modalStatusUsuarioIcon");
        const descEl = document.getElementById("modalStatusUsuarioDescricao");
        const nomeEl = document.getElementById("modalStatusUsuarioNome");
        const infoEl = document.getElementById("modalStatusUsuarioInfo");
        const avisoEl = document.getElementById("modalStatusUsuarioAviso");
        const formEl = document.getElementById("formStatusUsuario");
        const btnConfirmar = document.getElementById("btnConfirmarStatusUsuario");

        nomeEl.textContent = nomeUsuario || "Membro";
        infoEl.textContent = infoUsuario || "";
        formEl.setAttribute("action", url);

        if (acao === "ativar") {
            tituloEl.textContent = "Aprovar / Ativar Acesso";
            tituloEl.parentElement.className = "modal-title fw-bold d-flex align-items-center gap-2 text-success";
            iconeEl.className = "bi bi-person-check-fill fs-5 text-success";
            descEl.textContent = "Deseja aprovar e liberar o acesso deste membro ao sistema?";
            avisoEl.innerHTML = '<i class="bi bi-info-circle text-success me-1"></i> O membro poderá realizar login imediatamente após a confirmação.';
            btnConfirmar.className = "btn btn-success";
            btnConfirmar.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Sim, ativar acesso';
        } else {
            tituloEl.textContent = "Desativar Acesso";
            tituloEl.parentElement.className = "modal-title fw-bold d-flex align-items-center gap-2 text-warning-emphasis";
            iconeEl.className = "bi bi-person-x-fill fs-5 text-warning";
            descEl.textContent = "Deseja realmente suspender o acesso deste membro?";
            avisoEl.innerHTML = '<i class="bi bi-info-circle text-warning-emphasis me-1"></i> O histórico de registros e reivindicações será mantido, mas o login ficará bloqueado.';
            btnConfirmar.className = "btn btn-warning text-dark fw-semibold";
            btnConfirmar.innerHTML = '<i class="bi bi-slash-circle me-1"></i> Sim, desativar';
        }
    });
});