FROM python:2.7 AS builder

COPY ./techtrends/requirements.txt .

RUN pip install --user -r requirements.txt

FROM python:2.7-slim
WORKDIR /code

COPY --from=builder /root/.local /root/.local

COPY ./techtrends .

ENV PATH=/root/.local:$PATH

EXPOSE 3111/tcp
CMD [ "python", "./app.py" ]
