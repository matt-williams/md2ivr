FROM python:3.8

RUN apt update && apt install -y espeak libsndfile-dev && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/mozilla/TTS.git && cd TTS && pip install -r requirements.txt && python setup.py install && cd - && rm -rf TTS

RUN mkdir /work
WORKDIR /work

RUN pip install gdown
RUN mkdir data
RUN gdown --id 1dntzjWFg7ufWaTaFy80nRz-Tu02xWZos -O data/tts_model.pth.tar
RUN gdown --id 1Ty5DZdOc0F7OTGj9oJThYbL5iVu_2G0K -O data/vocoder_model.pth.tar
RUN gdown --id 11oY3Tv0kQtxK_JPgxrfesa99maVXHNxU -O data/scale_stats.npy

RUN pip install marko

ADD data/*.json data/
ADD *.py ./

ENTRYPOINT ["/usr/local/bin/python3", "/work/md2ivr.py"]
