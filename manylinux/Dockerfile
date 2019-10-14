FROM quay.io/pypa/manylinux2010_x86_64

RUN yum install -y make unzip wget

COPY . /io

WORKDIR /io

RUN make clips_source
RUN make install-clips

CMD "./manylinux/build-wheels.sh"
