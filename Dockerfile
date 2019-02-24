# it's offical so i'm using it + alpine so damn small
FROM python:3.7.2-alpine3.9

# copy the codebase
COPY . /reporter

# install required packages
RUN pip install -r /reporter/requirements.txt

#set python to be unbuffered
ENV PYTHONUNBUFFERED=1

# run the worker-manger
WORKDIR /reporter
CMD [ "python", "/reporter/reporter.py" ]