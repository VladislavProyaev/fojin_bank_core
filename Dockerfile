FROM python:3.10
WORKDIR /src
COPY . /src

RUN pip install --no-cache-dir -r requirements.txt
CMD python run.py
