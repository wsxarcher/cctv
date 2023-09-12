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

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y build-essential libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools
RUN apt-get install -y libpango1.0-dev libgraphene-1.0-dev libgtk-4-dev libcsound64-6.0 libcsound64-dev libdav1d-dev

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"

COPY gst-plugins-rs-main.tar.gz /
RUN tar -xvf gst-plugins-rs-main.tar.gz

WORKDIR /gst-plugins-rs-main

ENV CSOUND_LIB_DIR=/usr/lib/x86_64-linux-gnu/
RUN make install

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

#RUN git checkout 6694d87a23886182900cdb49876d98989cc6e16d

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

COPY project ./project

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

RUN poetry install

CMD ["start"]