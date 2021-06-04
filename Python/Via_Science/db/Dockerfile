FROM postgres:10.6-alpine
COPY seed_data.sql /docker-entrypoint-initdb.d/
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=123456
ENV POSTGRES_DB=postgres