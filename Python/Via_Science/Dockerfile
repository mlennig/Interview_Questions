FROM continuumio/miniconda3:4.7.12

RUN apt update && apt install curl -y

ADD server.py /deploy/code/
WORKDIR /deploy/code/

RUN pip install psycopg2-binary
RUN pip install tornado


ENTRYPOINT ["python" , "server.py"]