from setuptools import setup, find_packages
import os
from BrowserWrapper import __version__


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def get_requirements():
    return (
        open(os.path.join(os.path.dirname(__file__), "requirements.txt"))
        .read()
        .splitlines()
    )
print("!!!!!!!!")
print(get_requirements())

setup(
    name="BrowserWrapper", # Replace with your own username
    version=__version__,
    author="Michael Fessenden",
    author_email="MikeFez@gmail.com",
    description="A selenium driver wrapper simplifying interactions with page elements",
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/MikeFez/BrowserWrapper",
    packages=find_packages(exclude=["test"]),
    install_requires=get_requirements(),
    test_suite="test",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)