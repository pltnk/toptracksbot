FROM python:3.9-slim
WORKDIR /opt/toptracksbot
ENV PYTHONPATH "/opt/toptracksbot:$PYTHONPATH"
ENV PYTHONUNBUFFERED true
COPY requirements.txt /opt/toptracksbot/requirements.txt
RUN pip install --no-cache-dir --ignore-installed -r requirements.txt
COPY . /opt/toptracksbot
CMD python3 wait_for_db.py && python3 run.py
