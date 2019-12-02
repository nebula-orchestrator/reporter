# it's offical so i'm using it + alpine so damn small
FROM python:3.8.0-alpine3.10

# copy the codebase
COPY . /reporter

# install required packages
RUN pip install -r /reporter/requirements.txt

#set python to be unbuffered
ENV PYTHONUNBUFFERED=1

# run the worker-manger
WORKDIR /reporter
CMD [ "python", "/reporter/reporter.py" ]