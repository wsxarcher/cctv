ARG POETRY_VERSION=1.6.1
ARG BASE_IMAGE=python:3.11-bookworm

FROM $BASE_IMAGE as builder

ARG POETRY_VERSION
RUN pip install poetry==$POETRY_VERSION

ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root

FROM $BASE_IMAGE

ENV DEBIAN_FRONTEND=noninteractive

RUN sed -i -e's/ main/ main contrib non-free/g' /etc/apt/sources.list.d/debian.sources
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb -P /tmp/
RUN dpkg -i /tmp/cuda-keyring_1.1-1_all.deb && rm /tmp/cuda-keyring_1.1-1_all.deb
RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y build-essential libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools
RUN apt-get install -y libpango1.0-dev libgraphene-1.0-dev libgtk-4-dev libcsound64-6.0 libcsound64-dev libdav1d-dev
RUN apt-get install -y cuda-toolkit-11-7 libcudnn8=8.5.0.96-1+cuda11.7 cuda-cupti-11-7 libnccl2=2.14.3-1+cuda11.7
RUN apt-get install -y ffmpeg

RUN curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain=1.72.1 -y

ENV PATH="/root/.cargo/bin:${PATH}"

RUN git clone --recursive https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs.git

WORKDIR /gst-plugins-rs

RUN git checkout b12278e33452e2ddf5a8acb862c4f4695d562517

ENV CSOUND_LIB_DIR=/usr/lib/x86_64-linux-gnu/
RUN make install -j8

ARG POETRY_VERSION
RUN pip install poetry==$POETRY_VERSION

WORKDIR /app

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder /app/pyproject.toml ./pyproject.toml

WORKDIR /

RUN git clone https://github.com/opencv/opencv.git

WORKDIR /opencv

RUN git checkout 6694d87a23886182900cdb49876d98989cc6e16d

RUN mkdir build
WORKDIR /opencv/build

RUN apt-get install -y cmake

RUN cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D INSTALL_PYTHON_EXAMPLES=ON \
    -D INSTALL_C_EXAMPLES=OFF \
    -D PYTHON_EXECUTABLE=$(which python3) \
    -D BUILD_opencv_python2=OFF \
    -D CMAKE_INSTALL_PREFIX=$(python3 -c "import sys; print(sys.prefix)") \
    -D PYTHON3_EXECUTABLE=$(which python3) \
    -D PYTHON3_INCLUDE_DIR=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
    -D PYTHON3_PACKAGES_PATH=$(python3 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
    -D WITH_GSTREAMER=ON \
    -D BUILD_EXAMPLES=ON ..

RUN make install -j8

WORKDIR /app

ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN chown -R $USER_UID:$USER_GID .

USER $USERNAME

ADD --chown=$USER_UID:$USER_GID https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt /usr/src/ultralytics/
ADD --chown=$USER_UID:$USER_GID https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt /usr/src/ultralytics/
ADD --chown=$USER_UID:$USER_GID https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt /usr/src/ultralytics/
ADD --chown=$USER_UID:$USER_GID https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l.pt /usr/src/ultralytics/
ADD --chown=$USER_UID:$USER_GID https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8x.pt /usr/src/ultralytics/

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:$PATH"

COPY --chown=$USER_UID:$USER_GID project ./project

RUN poetry install

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["start"]