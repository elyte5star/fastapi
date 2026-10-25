API with FastAPI.

## Project Setup

 - Clone project with

  ```
  git clone git@github.com:elyte5star/FastAPI.git
  ```
  - Create file .env and set values for the environment variables below:

  ```
    LOG_LEVEL="INFO"
    RQ_URL="amqp://rabbitUser:elyteRQ@localhost:5672/"
    DB_DNS="postgresql://userExample:54321@localhost:5432/elyte"
    
  ```
  
- Create virtual environment

```
  python3 -m venv env
  source env/bin/activate

```
- Expose the application to POSTGRES Database at port 5432
- Expose the application to RabbitMQ at port 5672

```
```
- Install dependencies : pip install --upgrade pip && pip install -r requirements.txt
- Run the Application:  python run_worker.py

```
 