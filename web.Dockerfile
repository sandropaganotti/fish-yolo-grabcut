FROM ubuntu:18.04

# streamlit-specific commands for config
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# install Python and Pip
RUN apt-get update && \
    apt-get install -y \
    python3 python3-pip \
    libsm6 libxext6 libxrender-dev \
    ffmpeg wget python3-venv

# expose port 5000 for streamlit
EXPOSE 5000

# make app directory
WORKDIR /web

# create venv
RUN python3 -m venv /opt/venv

# copy requirements.txt
COPY requirements.txt ./requirements.txt

# upgrade pip
RUN /opt/venv/bin/python3 -m pip install --upgrade pip

# install dependencies
RUN /opt/venv/bin/python3 -m pip install -r requirements.txt

# download weights 
RUN wget https://pjreddie.com/media/files/yolov3.weights -P ./config

# copy all files over
COPY . .

# launch the web app
CMD /opt/venv/bin/python3 init.py 
