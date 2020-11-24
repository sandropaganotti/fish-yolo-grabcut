FROM ubuntu:18.04

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# install Python and Pip
RUN apt-get update && \
    apt-get install -y \
    python3.7 python3-pip \
    libsm6 libxext6 libxrender-dev \
    ffmpeg wget

# expose port 8501 for streamlit
EXPOSE 8501

# make app directiry
WORKDIR /web

# copy requirements.txt
COPY requirements.txt ./requirements.txt

# upgrade pip
RUN pip3 install --upgrade pip

# install dependencies
RUN pip3 install -r requirements.txt

# copy all files over
COPY . .

# download YOLO weights
RUN wget https://pjreddie.com/media/files/yolov3-tiny.weights -P ./yolo-fish/yolov3-tiny.weights

# launch flask web
CMD python3 init.py 