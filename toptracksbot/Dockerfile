FROM python:3.9-slim
ENV PYTHONPATH "/opt/toptracksbot:$PYTHONPATH"
ENV PYTHONUNBUFFERED true
COPY . /opt/toptracksbot
WORKDIR /opt/toptracksbot
RUN pip install --no-cache-dir --ignore-installed -r requirements.txt
CMD python3 bot.py
