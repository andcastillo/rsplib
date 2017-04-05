FROM python:2.7

COPY ./run.py  opt/rspsink/run.py
COPY ./RSPCollector.py  opt/rspsink/RSPCollector.py
WORKDIR opt/rspsink

ENTRYPOINT [ "python", "./run.py"]

CMD ["None"]