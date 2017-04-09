FROM  jupyter/datascience-notebook:latest

RUN pip install --upgrade pip
RUN pip install docker
RUN pip install websocket-client
#RUN pip install cryptography
#RUN pip install azure-storage
#RUN pip install s3
RUN pip install altair
#RUN pip install --upgrade notebook 
# need jupyter_client >= 4.2 for sys-prefix below
RUN jupyter nbextension install --sys-prefix --py vega

RUN pip list


ENTRYPOINT ["start-notebook.sh","--NotebookApp.token=''", "--NotebookApp.base_url=/ide/"]
