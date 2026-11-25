# API de Atividades da Mergington High School

Uma aplicação FastAPI super simples que permite aos alunos visualizar e se inscrever em atividades extracurriculares.

## Funcionalidades

- Visualizar todas as atividades extracurriculares disponíveis
- Inscrever-se em atividades
- Exibir anúncios vigentes e gerenciar anúncios com uma conta de professor

## Como começar

1. Instale as dependências:

   ```
   pip install -r requirements.txt
   ```

2. Execute a aplicação:

   ```
   uvicorn src.app:app --reload
   ```

3. Abra seu navegador e acesse:
   - Documentação da API: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

## Endpoints da API

| Método | Endpoint                                                          | Descrição                                                            |
| ------ | ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Obtém todas as atividades com detalhes e número atual de participantes |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Inscreve-se em uma atividade                                         |
| POST   | `/activities/{activity_name}/unregister`                          | Remove a inscrição de um estudante |
| GET    | `/activities/days`                                                | Lista os dias com atividades |
| POST   | `/auth/login`                                                     | Autentica o professor e cria um cookie de sessão |
| GET    | `/auth/check-session`                                             | Retorna o usuário da sessão atual |
| POST   | `/auth/logout`                                                    | Encerra a sessão atual |
| GET    | `/announcements`                                                  | Lista anúncios vigentes, sem autenticação |
| GET    | `/announcements/all`                                              | Lista todos os anúncios; requer sessão |
| POST   | `/announcements`                                                  | Cria um anúncio; requer sessão |
| PUT    | `/announcements/{id}`                                             | Atualiza um anúncio; requer sessão |
| DELETE | `/announcements/{id}`                                             | Exclui um anúncio; requer sessão |

Os métodos POST e PUT de anúncios recebem JSON com `message` (1 a 500 caracteres), `expires_at` (data obrigatória no formato `AAAA-MM-DD`) e `start_date` (data opcional no mesmo formato ou `null`). As datas são inclusivas e interpretadas no calendário local do servidor; a data de início não pode ser posterior à expiração. O cookie de sessão é HttpOnly e expira após 12 horas.

As respostas de anúncios incluem `id` e `status` (`active`, `scheduled` ou `expired`), além dos campos informados.

O login recebe JSON com `username` e `password`. A API de login agora usa o corpo da requisição, em vez de credenciais na URL; a verificação de sessão usa o cookie em vez do nome de usuário.

## Modelo de Dados

A aplicação usa um modelo de dados simples com identificadores significativos:

1. **Atividades** - Usa o nome da atividade como identificador:
   - Descrição
   - Horário
   - Número máximo de participantes permitidos
   - Lista de e-mails dos alunos inscritos

2. **Alunos** - Usa o e-mail como identificador:
   - Nome
   - Série

Os dados são armazenados no MongoDB local (`localhost:27017`). A inicialização cria um anúncio de exemplo uma única vez, com expiração no último dia do mês atual. Execute os comandos acima a partir da raiz do repositório, com o MongoDB em execução.
