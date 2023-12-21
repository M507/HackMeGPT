apt-get remove python3-blinker -y
pip3 install -r requirements.txt
pip3 install --upgrade requests
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
#docker-compose -f docker-compose.yml up 
docker-compose -f docker-compose.yml up -d
pip3 install -r requirements.txt
python3 -m spacy download en_core_web_sm