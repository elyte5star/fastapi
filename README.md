

## Project Setup

 - Clone project with

  ```
  git clone git@github.com:elyte5star/FastAPI.git
  ```
  - Create file .env and set values for the environment variables below:

  ```
    LOG_LEVEL="INFO"
    ALGORITHM="HS256"
    CORS_ORIGINS='["https://frontend.elyte.com", "https://elyte.com", "http://elyte.com", "http://*.elyte.com", "http://localhost", "http://elyte.com:8080", "http://elyte.com:3001", "https://localhost", "https://elyte.com:443", "https://elyte.com:4001", "http://localhost:3000","http://localhost:8000"]'
    JWT_SECRETKEY="7a3c54660456ff1137b652e498624dfa09a0ec12b4fc49d38b85465da15027a1"
    JWT_EXPIRE_MINUTES="160"
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES="43200"
    API_SECRET="295d51726d124a7601036ed4a8116418b8fa78e3188d8d1856d351fd27055d55"
    DB_URL="postgresql+asyncpg://userExample:54321@localhost:5432/elyte"
    DB_DNS="postgresql://userExample:54321@localhost:5432/elyte"
    CLIENT_URL="http://localhost:3000"
    LOG_PATH="./api.log"
    MAIL_USERNAME="elyte5star"
    MAIL_FROM="elyte5star@gmail.com"
    MAIL_PORT="587"
    MAIL_SERVER="smtp.gmail.com"
    MAIL_STARTTLS="true"
    MAIL_SSL_TLS="false"
    MAIL_FROM_NAME="E-COMMERCE APPLICATION"
    MAIL_PASSWORD="**********"
    RQ_URL="amqp://rabbitUser:elyteRQ@localhost:5672/"
    MSAL_CLIENT_ID="********"
    MSAL_TENANT_ID="********"
    MSAL_JWK_URL="https://login.microsoftonline.com/*********/discovery/v2.0/keys"
    MSAL_AUTH_URL="https://login.microsoftonline.com/*********/oauth2/v2.0/authorize"
    MSAL_TOKEN_URL="https://login.microsoftonline.com/********/oauth2/v2.0/token"
    MSAL_ISSUER="https://login.microsoftonline.com/*************/v2.0/"
    MSAL_SCOPE_NAME="api://**********/user_impersonation"
    MSAL_CLIENT_SECRET="***********"
    GOOGLE_CLIENT_ID="**********.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET="*************"
    GOOGLE_AUDIENCE="*************.apps.googleusercontent.com"
  ```
  ```

- Install dependencies: use poetry install

```

```
- Expose the application to POSTGRES Database at port 5432
- Expose the application to RabbitMQ at port 5672

```
```
- Run the Application:  fastapi dev main.py or create a docker image and run the container.
- Run the worker application in the consumer folder separately or create a docker image and run the container.

```
 
# fastapi
# fastapi
# fastapi
