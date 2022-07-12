FROM python:3.10-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
COPY  templates ./templates/
COPY  static ./static
COPY  assets ./assets

RUN mkdir output
RUN mkdir dump
RUN python create_db.py

EXPOSE 5000
EXPOSE 8050


<<<<<<< HEAD
CMD [ "python", "./WebNetdump.py" ]
=======
CMD [ "python", "./WebNetdump.py" ]
>>>>>>> 998a20c7bf2b38d70400bf7e71ed813e2d463185
