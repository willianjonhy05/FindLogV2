document.addEventListener('DOMContentLoaded', function () {
  const cnpjInput = document.getElementById('cnpj');

  if (cnpjInput) {
    cnpjInput.addEventListener('input', function (e) {
      let value = e.target.value.replace(/\D/g, ''); // Remove tudo que não é dígito
      
      // Aplica a máscara progressivamente
      if (value.length <= 14) {
        value = value.replace(/^(\d{2})(\d)/, '$1.$2');
        value = value.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
        value = value.replace(/\.(\d{3})(\d)/, '.$1/$2');
        value = value.replace(/(\d{4})(\d)/, '$1-$2');
      }
      
      e.target.value = value;
    });
  }
});


document.addEventListener('DOMContentLoaded', function () {
  const cpfInput = document.getElementById('cpf');

  if (cpfInput) {
    cpfInput.addEventListener('input', function (e) {
      let value = e.target.value;

      // Remove tudo o que não for dígito
      value = value.replace(/\D/g, "");

      // Limita a 11 dígitos
      if (value.length > 11) {
        value = value.slice(0, 11);
      }

      // Aplica a máscara (000.000.000-00)
      if (value.length > 9) {
        value = value.replace(/^(\d{3})(\d{3})(\d{3})(\d{2}).*/, "$1.$2.$3-$4");
      } else if (value.length > 6) {
        value = value.replace(/^(\d{3})(\d{3})(\d{3}).*/, "$1.$2.$3");
      } else if (value.length > 3) {
        value = value.replace(/^(\d{3})(\d{3}).*/, "$1.$2");
      }

      e.target.value = value;
    });
  }
});

document.addEventListener('DOMContentLoaded', function () {
  const telefoneInput = document.getElementById('telefone');

  if (telefoneInput) {
    telefoneInput.addEventListener('input', function (e) {
      let value = e.target.value.replace(/\D/g, ''); // Remove tudo que não é dígito
      
      // Limita o tamanho máximo a 11 dígitos (com DDD)
      if (value.length > 11) {
        value = value.substring(0, 11);
      }
      
      // Aplica a máscara dependendo do tamanho (fixo ou celular)
      if (value.length > 10) {
        // Celular com 9 dígitos: (XX) XXXXX-XXXX
        value = value.replace(/^(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
      } else if (value.length > 6) {
        // Fixo com 8 dígitos ou celular digitando: (XX) XXXX-XXXX (ou parcial)
        value = value.replace(/^(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
      } else if (value.length > 2) {
        // Apenas DDD e início: (XX) XXXX
        value = value.replace(/^(\d{2})(\d{0,5})/, '($1) $2');
      } else if (value.length > 0) {
        // Apenas DDD inicial: (XX
        value = value.replace(/^(\d*)/, '($1');
      }
      
      e.target.value = value;
    });
  }
});


document.addEventListener('DOMContentLoaded', function () {
  const emailInput = document.getElementById('email');

  if (emailInput) {
    emailInput.addEventListener('blur', function () {
      const emailValue = emailInput.value.trim();
      
      // Expressão regular padrão para validação de e-mail
      const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (emailValue !== '' && !regexEmail.test(emailValue)) {
        // Adiciona a classe de erro do Bootstrap se for inválido
        emailInput.classList.add('is-invalid');
        
        // Opcional: exibe um alerta ou foca no campo
        // alert('Por favor, insira um e-mail válido.');
      } else {
        // Remove o erro se estiver correto ou vazio
        emailInput.classList.remove('is-invalid');
      }
    });

    // Remove o erro assim que o usuário começar a corrigir digitando novamente
    emailInput.addEventListener('input', function () {
      emailInput.classList.remove('is-invalid');
    });
  }
});