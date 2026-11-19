document.addEventListener("DOMContentLoaded", function () {
    const selectTipo = document.getElementById("id_tipo");
    const containerSala = document.getElementById("container-sala");
    const inputSala = document.getElementById("id_sala");
    const inputCpf = document.getElementById("id_cpf");
    const inputTelefone = document.getElementById("id_telefone");

    // 1. Alterna visibilidade, obrigatoriedade e limpeza do campo Sala
    function ajustarCampoDeSala() {
        if (!selectTipo || !containerSala) return;

        // Valor 3 corresponde a Perfil.TipoUsuario.SERVIDOR
        const ehServidor = selectTipo.value === "3";
        containerSala.style.display = ehServidor ? "block" : "none";

        if (inputSala) {
            inputSala.required = ehServidor;
            if (!ehServidor) {
                inputSala.value = "";
            }
        }
    }

    if (selectTipo) {
        selectTipo.addEventListener("change", ajustarCampoDeSala);
        ajustarCampoDeSala();
    }

    // 2. Máscara progressiva de CPF: 000.000.000-00
    function aplicarMascaraCpf(valor) {
        const digitos = String(valor).replace(/\D/g, "").slice(0, 11);
        if (digitos.length > 9) {
            return digitos.replace(/^(\d{3})(\d{3})(\d{3})(\d{1,2})$/, "$1.$2.$3-$4");
        } else if (digitos.length > 6) {
            return digitos.replace(/^(\d{3})(\d{3})(\d{1,3})$/, "$1.$2.$3");
        } else if (digitos.length > 3) {
            return digitos.replace(/^(\d{3})(\d{1,3})$/, "$1.$2");
        }
        return digitos;
    }

    if (inputCpf) {
        if (inputCpf.value) {
            inputCpf.value = aplicarMascaraCpf(inputCpf.value);
        }
        inputCpf.addEventListener("input", function () {
            this.value = aplicarMascaraCpf(this.value);
        });
    }

    // 3. Máscara progressiva de Telefone/WhatsApp: (00) 0000-0000 ou (00) 00000-0000
    function aplicarMascaraTelefone(valor) {
        const digitos = String(valor).replace(/\D/g, "").slice(0, 11);
        if (digitos.length === 0) return "";
        if (digitos.length <= 2) return `(${digitos}`;
        if (digitos.length <= 6) return `(${digitos.slice(0, 2)}) ${digitos.slice(2)}`;
        if (digitos.length <= 10) {
            return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 6)}-${digitos.slice(6)}`;
        }
        return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 7)}-${digitos.slice(7, 11)}`;
    }

    if (inputTelefone) {
        if (inputTelefone.value) {
            inputTelefone.value = aplicarMascaraTelefone(inputTelefone.value);
        }
        inputTelefone.addEventListener("input", function () {
            this.value = aplicarMascaraTelefone(this.value);
        });
    }
});