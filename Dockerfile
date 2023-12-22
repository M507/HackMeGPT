FROM python:3.8

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/C=GB/ST=London/L=London/O=Global Security/OU=IT Department/CN=example.com"
RUN python -m spacy download en_core_web_sm

COPY . .

CMD ["python", "./app.py"]