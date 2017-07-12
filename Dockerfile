FROM gcr.io/tensorflow/tensorflow:latest-gpu

RUN apt-get update

# install python packages
RUN pip install scikit-learn jupyter keras
