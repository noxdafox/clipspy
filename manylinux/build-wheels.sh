#!/bin/bash

PLATFORM=manylinux2014_x86_64

set -e -x

function repair_wheel {
    wheel="$1"
    if ! auditwheel show "$wheel"; then
        echo "Skipping non-platform wheel $wheel"
    else
        auditwheel repair "$wheel" --plat "$PLATFORM" -w /io/wheelhouse/
    fi
}

# Compile wheels
for PYBIN in /opt/python/*/bin; do
    if [[ ! $PYBIN =~ 313 ]]; then
        "${PYBIN}/pip" install cffi pytest setuptools
        "${PYBIN}/pip" wheel /io/ --no-deps -w wheelhouse/
    fi
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    repair_wheel "$whl"
done

# Install packages and test
for PYBIN in /opt/python/*/bin; do
    if [[ ! $PYBIN =~ 313 ]]; then
        "${PYBIN}/pip" install clipspy --no-index -f /io/wheelhouse
        (cd "$HOME"; "${PYBIN}/pytest" -v /io/test)
    fi
done
