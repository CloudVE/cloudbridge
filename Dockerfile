ARG EXTRA=full
ARG PYTHON=3.9

FROM python:$PYTHON-slim
RUN pip install --no-cache-dir cloudbridge[$EXTRA]

COPY scripts/ cloudbridge_scripts/
