#!/usr/bin/env bash
set -xe

py_platform=$(python -c "import sysconfig; print('%s' % sysconfig.get_platform());")

echo " - Python platform: ${py_platform}"
if [[ "${py_platform}" == *"-universal2" ]]; then
    if [[ `uname -m` == 'arm64' ]]; then
        export _PYTHON_HOST_PLATFORM="${py_platform/universal2/arm64}"
        echo " - Python installation is universal2 and we are on arm64, setting _PYTHON_HOST_PLATFORM to: ${_PYTHON_HOST_PLATFORM}"
        export ARCHFLAGS="-arch arm64"
        echo " - Setting ARCHFLAGS to: ${ARCHFLAGS}"
        # This is a shortcut to have a successful delocate-wheel. See:
        # https://github.com/matthew-brett/delocate/issues/153
        python -c "import os,delocate; print(os.path.join(os.path.dirname(delocate.__file__), 'tools.py'));quit()"  | xargs -I{} sed -i."" "s/first, /input.pop('x86_64',None); first, /g" {}
    else
        export _PYTHON_HOST_PLATFORM="${py_platform/universal2/x86_64}"
        echo " - Python installation is universal2 and we are on x84_64, setting _PYTHON_HOST_PLATFORM to: ${_PYTHON_HOST_PLATFORM}"
        export ARCHFLAGS="-arch x86_64"
        echo " - Setting ARCHFLAGS to: ${ARCHFLAGS}"
    fi
fi

python setup.py build_ext --include-dirs=clips_source/ --library-dirs=clips_source/ bdist_wheel

delocate-listdeps dist/*.whl

delocate-wheel -v dist/*.whl
