ARG PYVER=python.version
ARG DEBIANVER=os.version
ARG PREBUILT_PKG=package.version

FROM python:${PYVER}-${DEBIANVER}

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /cse-multimodal-app

COPY packages/${PREBUILT_PKG} /cse-multimodal-app/${PREBUILT_PKG}
COPY requirements.txt /cse-multimodal-app/requirements.txt
COPY llava_player.py /cse-multimodal-app/llava_player.py

RUN pip3 install -r requirements.txt && \
    rm -rf /root/.cache

CMD [ "/bin/bash" ]