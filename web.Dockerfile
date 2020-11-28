FROM ubuntu:18.04

# streamlit-specific commands for config
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# install Python and Pip
RUN apt-get update && \
    apt-get install -y \
    python3.7 python3-pip \
    libsm6 libxext6 libxrender-dev \
    ffmpeg wget

# expose port 5000 for streamlit
EXPOSE 5000

# make app directory
WORKDIR /web

# copy requirements.txt
COPY requirements.txt ./requirements.txt

# upgrade pip
RUN python3.7 -m pip install --upgrade pip

# install dependencies
RUN python3.7 -m pip install -r requirements.txt

# upgrade setuptools 
RUN python3.7 -m pip install --upgrade setuptools

# fix heroku permission issues 
RUN chmod 777 /usr/lib/python3/dist-packages/.wh.six-1.11.0.egg-info

# download weights 
RUN wget https://pjreddie.com/media/files/yolov3.weights -P ./config

# copy all files over
COPY . .

# launch the web app
CMD python3.7 init.py 
