FROM bitnami/python:3.8
RUN python3.8 -m pip install httpx
COPY trigger.py /entrypoint.py
ENTRYPOINT ["/entrypoint.py"]