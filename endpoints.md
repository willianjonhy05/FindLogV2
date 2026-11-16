# 📱 Guia de Integração da API de Autenticação - FindLog

Este documento descreve os endpoints de autenticação baseados em **JWT (JSON Web Tokens)** para consumo por aplicativos móveis (Flutter, React Native, Nativo).

* **Base URL de Desenvolvimento:** `http://localhost:8000/api/v1/`
* **Formato de Envio/Resposta:** `application/json`

---

## 1. Autenticar Usuário (Login)
Autentica o usuário utilizando e-mail e senha, retornando os tokens de acesso e renovação, além de dados básicos do perfil.

* **Método:** `POST`
* **Rota:** `/auth/login/`
* **Autenticação:** Não requer autenticação (`AllowAny`).

### Exemplo de Requisição (Body)
```json
{
  "email": "usuario@exemplo.com",
  "password": "sua_senha_secreta"
}
```

### Exemplo de Resposta (Sucesso - `200 OK`)
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "nome": "João da Silva",
  "email": "usuario@exemplo.com",
  "tipo": 2,
  "username": "joao.silva"
}
```

### Exemplo de Resposta (Erro / Credenciais Inválidas - `401 Unauthorized`)
```json
{
  "detail": "Nenhuma conta encontrada com as credenciais dadas."
}
```

---

## 2. Renovar Token de Acesso (Refresh Token)
Utiliza o `refresh` token para gerar um novo `access` token válido, sem que o usuário precise digitar a senha novamente.

* **Método:** `POST`
* **Rota:** `/auth/refresh/`
* **Autenticação:** Não requer autenticação.

### Exemplo de Requisição (Body)
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Exemplo de Resposta (Sucesso - `200 OK`)
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## 3. Consultar Dados do Usuário Logado (Me)
Retorna as informações cadastrais detalhadas do perfil associado ao token de acesso atual.

* **Método:** `GET`
* **Rota:** `/auth/me/`
* **Autenticação:** **Obrigatória** (Enviar Header HTTP).

### Exemplo de Requisição (Headers)
```http
Authorization: Bearer <seu_access_token_aqui>
```

### Exemplo de Resposta (Sucesso - `200 OK`)
```json
{
  "id": 15,
  "username": "joao.silva",
  "nome": "João da Silva",
  "email": "usuario@exemplo.com",
  "cpf": "52998224725",
  "tipo": 2,
  "ativo": true
}
```

---

## 4. Encerrar Sessão (Logout)
Invalida o token de atualização (`refresh_token`) adicionando-o à lista negra (*blacklist*) no servidor.

* **Método:** `POST`
* **Rota:** `/auth/logout/`
* **Autenticação:** **Obrigatória** (Enviar Header HTTP).

### Exemplo de Requisição (Headers & Body)
```http
Authorization: Bearer <seu_access_token_aqui>
Content-Type: application/json
```
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Exemplo de Resposta (Sucesso - `200 OK`)
```json
{
  "message": "Sessão encerrada com sucesso."
}
```

---

## 💡 Boas Práticas para o Desenvolvedor Mobile

1. **Armazenamento Seguro:** Guarde os tokens `access` e `refresh` utilizando bibliotecas nativas de armazenamento seguro (como `flutter_secure_storage` no Flutter ou `EncryptedSharedPreferences` no Android).
2. **Interceptors HTTP:** Configure um interceptador nas requisições do aplicativo (ex: Dio ou Axios) para anexar automaticamente o cabeçalho `Authorization: Bearer <token>` em todas as rotas protegidas.
3. **Renovação Automática:** Se uma requisição retornar erro `401 Unauthorized` por expiração do token de acesso, o app deve disparar automaticamente uma requisição para `/auth/refresh/` usando o `refresh` token salvo, repetir a requisição original e, caso o `refresh` expire, forçar o redirecionamento para a tela de login.