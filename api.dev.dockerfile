FROM python:3.13

WORKDIR /usr/src

RUN mkdir -p /logs 


# Copy only requirements to cache them in docker layer:
# Usage: COPY [from, from, from, to]
COPY ["./api/src/pyproject.toml", "./"]

# Set the python path:
ENV PYTHONPATH="$PYTHONPATH:${PWD}"

RUN pip install --upgrade pip && pip install poetry==1.8.2 --break components

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000","--reload"]

EXPOSE 8000
