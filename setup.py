from setuptools import setup

setup(
    name="clipspy",
    version="0.0.1",
    author="Matteo Cafasso",
    author_email="noxdafox@gmail.com",
    description=("CLIPS Python bindings."),
    setup_requires=["cffi>=1.0.0"],
    install_requires=["cffi>=1.0.0"],
    cffi_modules=["clips/clips_build.py:ffibuilder"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License"
    ]
)
