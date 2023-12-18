FROM python:3.8

WORKDIR /vlan_configurator
COPY Vlan_configurator/requirements.txt vlan_configurator/requirements.txt

RUN mkdir __logger

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
#RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN wget -O /tmp/chromedriver-linux64.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/119.0.6045.105/linux64/chromedriver-linux64.zip
RUN unzip /tmp/chromedriver-linux64.zip "chromedriver-linux64/chromedriver" -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99

RUN pip install --upgrade pip

RUN pip install -r vlan_configurator/requirements.txt

#CMD ["python", "./__init__.py"]
