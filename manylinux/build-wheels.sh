#!/bin/bash

PLATFORM=manylinux2014_x86_64

set -e -x

# Compile wheels
for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/pip" install cffi pytest setuptools
    "${PYBIN}/pip" wheel /io/ --no-deps -w wheelhouse/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    if ! auditwheel show "$whl"; then
        echo "Skipping non-platform wheel $whl"
    else
        auditwheel repair "$whl" --plat "$PLATFORM" -w /io/wheelhouse/
    fi
done

# Install packages and test
for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/pip" install clipspy --no-index -f /io/wheelhouse
    (cd "$HOME"; "${PYBIN}/pytest" -v /io/test)
done
