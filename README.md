# Sistema de Agendamento de Salas

Este é um sistema de agendamento de salas desenvolvido em Python com interface gráfica utilizando a biblioteca `customtkinter`. O sistema permite gerenciar reservas de salas, incluindo criação, edição e exclusão de agendamentos.

## Requisitos

Antes de executar o projeto, certifique-se de que você possui os seguintes requisitos instalados:

- Python 3.10 ou superior
- PostgreSQL

## Configuração do Banco de Dados

1. Crie um banco de dados no PostgreSQL para o sistema.
2. Configure as credenciais de acesso ao banco de dados nos arquivos Python do projeto. Atualize as variáveis a seguir nos arquivos `src/Reserva_de_Sala.py` e `src/Administrar_Agendamento.py`:

   ```python
   DB_NAME = "nome_do_banco"
   DB_USER = "usuario"
   DB_PASSWORD = "senha"
   DB_HOST = "host"
   DB_PORT = "porta"
   ```

3. Certifique-se de que a tabela `reservas` existe no banco de dados com a seguinte estrutura:

   ```sql
   CREATE TABLE reservas (
       id SERIAL PRIMARY KEY,
       nome VARCHAR(255) NOT NULL,
       data DATE NOT NULL,
       inicio TIME NOT NULL,
       fim TIME NOT NULL,
       bebida VARCHAR(255),
       inicio_completo TIMESTAMP,
       fim_completo TIMESTAMP
   );
   ```

## Instalação de Dependências

Instale as dependências do projeto utilizando o arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Executando o Projeto

1. Navegue até o diretório `src`.
2. Execute o arquivo `Recepcao.py` para iniciar a interface principal:

```bash
python Recepcao.py
```

## Estrutura do Projeto

- `src/Administrar_Agendamento.py`: Interface para gerenciar (editar/excluir) agendamentos.
- `src/Reserva_de_Sala.py`: Lógica adicional para reservas.
- `requirements.txt`: Lista de dependências do projeto.

## Observações

- Certifique-se de que o servidor PostgreSQL está em execução antes de iniciar o sistema.
- Caso encontre problemas, verifique as configurações de conexão com o banco de dados e as dependências instaladas.

## Licença

Este projeto é de uso interno e não possui uma licença pública.
