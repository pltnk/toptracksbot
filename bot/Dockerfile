FROM python:3.9-slim
WORKDIR /opt/toptracksbot/bot
ENV PYTHONPATH "/opt/toptracksbot:$PYTHONPATH"
ENV PYTHONUNBUFFERED true
COPY requirements.txt /opt/toptracksbot/bot/requirements.txt
RUN pip install --no-cache-dir --ignore-installed -r requirements.txt
COPY . /opt/toptracksbot/bot
CMD python3 wait_for_db.py && python3 run.py
