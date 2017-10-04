from setuptools import find_packages, setup

setup(
    name="clipspy",
    version="0.0.1",
    author="Matteo Cafasso",
    author_email="noxdafox@gmail.com",
    description=("CLIPS Python bindings."),
    packages=find_packages(),
    ext_package="clips",
    setup_requires=["cffi>=1.0.0"],
    install_requires=["cffi>=1.0.0"],
    cffi_modules=["clips_build.py:ffibuilder"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License"
    ]
)
