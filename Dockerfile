FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .
COPY  templates ./templates/
COPY  static ./static
COPY  assets ./assets

RUN mkdir output
RUN mkdir dump

EXPOSE 5000
EXPOSE 8050

CMD [ "python", "./WebNetdump.py" ]