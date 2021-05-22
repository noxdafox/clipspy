FROM quay.io/pypa/manylinux2014_x86_64

RUN yum install -y make unzip wget libffi libffi-devel

COPY . /io

WORKDIR /io

RUN make install-clips

CMD "./manylinux/build-wheels.sh"
