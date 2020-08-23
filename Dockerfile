FROM python:3.8

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

RUN python setup.py install
RUN mkdir /data

ENTRYPOINT [ "/usr/src/app/create_keys.py" ]
