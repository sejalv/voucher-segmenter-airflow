FROM python:3.8
#
#RUN mkdir -p /opt/voucher
#
#WORKDIR /opt/voucher

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "app.py" ]