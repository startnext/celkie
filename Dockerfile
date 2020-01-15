FROM python:3.7.6-alpine3.10

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY celkie.py /usr/local/bin/
COPY celkie.yaml /usr/local/bin/

ENTRYPOINT [ "python", "/usr/local/bin/celkie.py" ]
