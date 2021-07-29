FROM python:3.9-slim
WORKDIR /opt/toptracksbot
ENV PYTHONPATH "/opt/toptracksbot:$PYTHONPATH"
ENV PYTHONUNBUFFERED true
COPY ./bot/requirements.txt /opt/toptracksbot/bot/requirements.txt
RUN pip install --no-cache-dir --ignore-installed -r /opt/toptracksbot/bot/requirements.txt
COPY ./tests/requirements.txt /opt/toptracksbot/tests/requirements.txt
RUN pip install --no-cache-dir --ignore-installed -r /opt/toptracksbot/tests/requirements.txt
COPY . /opt/toptracksbot
CMD python3 ./bot/wait_for_db.py && pytest ./tests/test_storing.py -v
