# FindLog V2

Sistema de gerenciamento de achados e perdidos desenvolvido para instituições e empresas.

## 🚀 Como Executar o Projeto

Siga os passos abaixo para configurar e rodar o projeto localmente em sua máquina (ambiente Windows):

### Passo 1
Escolha e acesse uma pasta de sua preferência no seu computador.

### Passo 2
Abra o terminal na pasta escolhida e execute o comando para clonar o repositório:

```
git clone https://github.com/willianjonhy05/FindLogV2.git
```

### Passo 3
Entre na pasta do projeto recém-criada:

```
cd FindLogV2
```

### Passo 4
Crie e ative o ambiente virtual Python executando os comandos:

```
python -m venv venv
./venv/Scripts/activate

```

### Passo 5
Com o ambiente virtual ativado, instale as dependências do projeto:

```
pip install -r requirements.txt
```

### Passo 6

Acesse o arquivo .env.example e copie o conteúdo. Depois crie o arquivo .env e cole o conteúdo copiado


Entre no site [https://randomkeygen.com/flask-secret-key??????](https://djecrety.ir/) e gere uma chave secreta. Copie o código, vá no seu arquivo .env e crie a seguinte variável: 


```
SECRET_KEY=cole_aqui_o_codigo gerado

```

### Passo 7

No seu terminal, com o ambiente virtual ativado execute a sequencia de dois comandos a seguir

```
python manage.py makemigrations

python manage.py migrate
```


### Passo 8

Agora você precisa criar uma senha de administrador. Utilize o comando:

```
python manage.py createsuperuser
```

Você será solicitado para preencher campos com email, nome de usuário (use somente o primeiro nome sem acento) e criar uma senha (enquanto digita esse campo ficará oculto e seus digitoss não aparecerão)


### Passo 9

Agora você pode rodar o comando para verificar o site: 

```
python manage.py runserver
```

Acesse o endereço: http://localhost:8000/ acesse a página de login e use o email e senha que você acabou de criar.


Se obtiver algum erro, por favor, faça print da página e entre em contato imediatamente com o William


Pronto! O sistema estará rodando e disponível para acesso no seu navegador através do endereço gerado pelo Django.

Projeto desenvolvido pela Equipe Primeira Classe de Desenvolvimento.
