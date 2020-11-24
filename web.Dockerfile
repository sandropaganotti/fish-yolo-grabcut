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
RUN pip3 install --upgrade pip

# install dependencies
RUN pip3 install -r requirements.txt

# copy all files over
COPY . .

# launch the web app
CMD python3 init.py 
