# Copyright (c) 2016-2018, Matteo Cafasso
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import subprocess
from setuptools import find_packages, setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def package_version():
    """Get the package version via Git Tag."""
    version_path = os.path.join(os.path.dirname(__file__), 'version.py')

    version = read_version(version_path)
    write_version(version_path, version)

    return version


def read_version(path):
    try:
        return subprocess.check_output(('git', 'describe')).rstrip().decode()
    except Exception:
        with open(path) as version_file:
            version_string = version_file.read().split('=')[-1]
            return version_string.strip().replace('"', '')


def write_version(path, version):
    msg = '"""Versioning controlled via Git Tag, check setup.py"""'
    with open(path, 'w') as version_file:
        version_file.write(msg + os.linesep + os.linesep +
                           '__version__ = "{}"'.format(version) +
                           os.linesep)


setup(
    name="clipspy",
    version="{}".format(package_version()),
    author="Matteo Cafasso",
    author_email="noxdafox@gmail.com",
    description=("CLIPS Python bindings"),
    license="BSD",
    long_description=read('README.rst'),
    packages=find_packages(),
    ext_package="clips",
    setup_requires=["cffi>=1.0.0"],
    install_requires=["cffi>=1.0.0"],
    extras_require={":python_version<'3'": ["enum34"]},
    cffi_modules=["clips/clips_build.py:ffibuilder"],
    include_dirs=["/usr/include/clips", "/usr/local/include/clips"],
    data_files=[('lib', ['lib/clips.c', 'lib/clips.cdef'])],
    keywords="clips python cffi expert-system",
    url="https://github.com/noxdafox/clipspy",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License"
    ]
)
