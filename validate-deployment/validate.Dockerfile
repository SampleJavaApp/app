FROM python:3.9-slim

WORKDIR /app

RUN pip install flask

COPY . .

EXPOSE 443

CMD ["python", "validate.py"]
