document.addEventListener("DOMContentLoaded", function () {
  // Função para formatar CNPJ: 00.000.000/0000-00
  function formatarCNPJ(cnpj) {
    const valor = String(cnpj).replace(/\D/g, "");
    if (valor.length !== 14) return cnpj;
    return valor.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
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
    let valor = String(cpf).replace(/\D/g, "").slice(0, 11);

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

  // 1. Formatação em elementos de texto estático (tabelas, cards, spans)
  document.querySelectorAll(".cnpj-format").forEach(function (el) {
    if (el.textContent.trim()) {
      el.textContent = formatarCNPJ(el.textContent.trim());
    }
  });

  document.querySelectorAll(".telefone-format").forEach(function (el) {
    if (el.textContent.trim()) {
      el.textContent = formatarTelefone(el.textContent.trim());
    }
  });

  document.querySelectorAll(".cpf-format").forEach(function (el) {
    if (el.textContent.trim()) {
      el.textContent = formatarCPF(el.textContent.trim());
    }
  });

  document.querySelectorAll(".data").forEach(function (el) {
    if (el.textContent.trim()) {
      el.textContent = formataData(el.textContent.trim());
    }
  });

  // 2. Máscara dinâmica e inicial para o campo <input id="id_telefone">
  const inputTelefone = document.getElementById("telefone");
  if (inputTelefone) {
    if (inputTelefone.value) {
      inputTelefone.value = formatarTelefone(inputTelefone.value);
    }

    inputTelefone.addEventListener("input", function () {
      this.value = formatarTelefone(this.value);
    });
  }
});