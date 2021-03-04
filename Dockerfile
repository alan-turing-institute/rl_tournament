FROM ubuntu:18.04

### get pip git etc

RUN apt-get update; apt-get install -y python3
RUN apt-get update; apt-get install -y python3-pip
RUN apt-get update; apt-get install -y locales

RUN apt-get update; apt-get install -y git
RUN apt-get update; apt-get install -y libgl1-mesa-glx
RUN apt-get update; apt-get install -y nano

# Set the locale
RUN sed -i -e 's/# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG en_GB.UTF-8
ENV LANGUAGE en_GB:en
ENV LC_ALL en_GB.UTF-8

ADD requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /tmp/requirements.txt

ADD . /rl_tournament
WORKDIR /rl_tournament

RUN git clone https://github.com/alan-turing-institute/plark_ai_public
RUN cd plark_ai_public/Components/plark-game; pip3 install .

### TOTAL HACK - MUST BE A BETTER WAY TO INSTALL resources/font.tff
RUN cp -r plark_ai_public/Components/plark-game/plark_game/classes/resources /usr/local/lib/python3.6/dist-packages/plark_game/classes/