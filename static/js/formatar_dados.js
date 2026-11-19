document.addEventListener("DOMContentLoaded", function () {
  // Função para formatar CNPJ progressivamente ou completo: 00.000.000/0000-00
  function formatarCNPJ(cnpj) {
    const valor = String(cnpj).replace(/\D/g, "").slice(0, 14);

    if (valor.length > 12) {
      return valor.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{1,2})$/, "$1.$2.$3/$4-$5");
    } else if (valor.length > 8) {
      return valor.replace(/^(\d{2})(\d{3})(\d{3})(\d{1,4})$/, "$1.$2.$3/$4");
    } else if (valor.length > 5) {
      return valor.replace(/^(\d{2})(\d{3})(\d{1,3})$/, "$1.$2.$3");
    } else if (valor.length > 2) {
      return valor.replace(/^(\d{2})(\d{1,3})$/, "$1.$2");
    }

    return valor;
  }

  // Função para formatar Data: AAAA-MM-DD -> DD/MM/AAAA
  function formataData(data) {
    if (!data) return "Não informada";
    const textoData = String(data).trim();

    if (/^\d{4}-\d{2}-\d{2}$/.test(textoData)) {
      const [ano, mes, dia] = textoData.split("-");
      return `${dia}/${mes}/${ano}`;
    }

    return data;
  }

  // Função para formatar CPF progressivamente ou completo: 000.000.000-00
  function formatarCPF(cpf) {
    const valor = String(cpf).replace(/\D/g, "").slice(0, 11);

    if (valor.length > 9) {
      return valor.replace(/^(\d{3})(\d{3})(\d{3})(\d{1,2})$/, "$1.$2.$3-$4");
    } else if (valor.length > 6) {
      return valor.replace(/^(\d{3})(\d{3})(\d{1,3})$/, "$1.$2.$3");
    } else if (valor.length > 3) {
      return valor.replace(/^(\d{3})(\d{1,3})$/, "$1.$2");
    }

    return valor;
  }

  // Função para formatar Telefone/Celular progressivamente ou completo: (00) 0000-0000 / (00) 00000-0000
  function formatarTelefone(telefone) {
    const digitos = String(telefone).replace(/\D/g, "").slice(0, 11);

    if (digitos.length === 0) return "";
    if (digitos.length <= 2) return `(${digitos}`;
    if (digitos.length <= 6) return `(${digitos.slice(0, 2)}) ${digitos.slice(2)}`;
    if (digitos.length <= 10) {
      return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 6)}-${digitos.slice(6)}`;
    }
    return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 7)}-${digitos.slice(7, 11)}`;
  }

  // Helper: aplica a função tanto em texto estático (td/span) quanto em <input> (inicial + digitação)
  function vincularFormatacao(seletor, fnFormatadora) {
    document.querySelectorAll(seletor).forEach(function (el) {
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        if (el.value) {
          el.value = fnFormatadora(el.value);
        }
        el.addEventListener("input", function () {
          this.value = fnFormatadora(this.value);
        });
      } else if (el.textContent.trim()) {
        el.textContent = fnFormatadora(el.textContent.trim());
      }
    });
  }

  // 1. Aplica por classes (.cnpj-format, .telefone-format, .cpf-format) em textos e inputs
  vincularFormatacao(".cnpj-format", formatarCNPJ);
  vincularFormatacao(".cpf-format", formatarCPF);
  vincularFormatacao('.telefone-format, #telefone, #id_telefone, input[name="telefone"]', formatarTelefone);

  // 2. Formatação de datas estáticas (YYYY-MM-DD -> DD/MM/YYYY)
  document.querySelectorAll(".data").forEach(function (el) {
    if (el.textContent.trim()) {
      el.textContent = formataData(el.textContent.trim());
    }
  });
});