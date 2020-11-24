FROM python:3.9

LABEL "maintainer"="Leandro Benedet Garcia <cerberus1746@gmail.com>"

RUN python -m pip install -U pip

ADD entrypoint.py /entrypoint.py
ADD sphinx_action /sphinx_action

ENTRYPOINT ["/entrypoint.py"]
