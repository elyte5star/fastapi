FROM python:3.13

WORKDIR /usr/src

COPY requirements.txt requirements.txt

# Set the python path:
#ENV PYTHONPATH="$PYTHONPATH:${PWD}"

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ["./src", "./"]

CMD ["python", "-u", "run_worker.py"]

