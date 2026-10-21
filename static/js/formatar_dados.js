document.addEventListener('DOMContentLoaded', function () {
  // Função para formatar CNPJ: 00.000.000/0000-00
  function formatarCNPJ(cnpj) {
    let valor = cnpj.replace(/\D/g, '');
    if (valor.length !== 14) return cnpj; // Retorna o original se não tiver 14 dígitos
    return valor.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
  }

  function formataData(data) {
    if (!data) return 'Não informada';

    let textoData = String(data).trim();

    // Verifica se está no formato AAAA-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(textoData)) {
      let partes = textoData.split('-');
      let ano = partes[0];
      let mes = partes[1];
      let dia = partes[2];

      return `${dia}/${mes}/${ano}`;
    }

    // Retorna o valor original caso não bata com o formato esperado
    return data;
  }

  function formatarCPF(cpf) {
    // Remove tudo o que não for dígito
    let valor = cpf.replace(/\D/g, "");

    // Limita a 11 dígitos caso venha maior
    if (valor.length > 11) {
      valor = valor.slice(0, 11);
    }

    // Aplica a máscara progressivamente conforme o tamanho
    if (valor.length === 11) {
      valor = valor.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4");
    } else if (valor.length > 9) {
      valor = valor.replace(/^(\d{3})(\d{3})(\d{3})(\d{2}).*/, "$1.$2.$3-$4");
    } else if (valor.length > 6) {
      valor = valor.replace(/^(\d{3})(\d{3})(\d{3}).*/, "$1.$2.$3");
    } else if (valor.length > 3) {
      valor = valor.replace(/^(\d{3})(\d{3}).*/, "$1.$2");
    }

    return valor;
  }

  // Função para formatar Telefone/Celular: (00) 0000-0000 ou (00) 00000-0000
  function formatarTelefone(telefone) {
    let valor = telefone.replace(/\D/g, '');

    if (valor.length === 11) {
      // Celular: (XX) XXXXX-XXXX
      return valor.replace(/^(\d{2})(\d{5})(\d{4})$/, '($1) $2-$3');
    } else if (valor.length === 10) {
      // Fixo: (XX) XXXX-XXXX
      return valor.replace(/^(\d{2})(\d{4})(\d{4})$/, '($1) $2-$3');
    }
    return telefone; // Retorna o original se não se enquadrar
  }

  // Aplica a formatação nos elementos que possuem a classe 'cnpj-format'
  document.querySelectorAll('.cnpj-format').forEach(function (td) {
    if (td.textContent) {
      td.textContent = formatarCNPJ(td.textContent.trim());
    }
  });

  // Aplica a formatação nos elementos que possuem a classe 'telefone-format'
  document.querySelectorAll('.telefone-format').forEach(function (td) {
    if (td.textContent) {
      td.textContent = formatarTelefone(td.textContent.trim());
    }
  });

  // Aplica a formatação nos elementos que possuem a classe 'cpf-format'
  document.querySelectorAll('.cpf-format').forEach(function (td) {
    if (td.textContent) {
      td.textContent = formatarCPF(td.textContent.trim());
    }
  });

  // Aplica a formatação nos elementos que possuem a classe 'data'
  document.querySelectorAll('.data').forEach(function (td) {
    if (td.textContent) {
      td.textContent = formataData(td.textContent.trim());
    }
  });

});