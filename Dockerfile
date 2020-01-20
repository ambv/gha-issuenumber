FROM bitnami/python:3.8
RUN python3.8 -m pip install dulwich
COPY entrypoint.py /entrypoint.py
ENTRYPOINT ["/entrypoint.py"]