from setuptools import setup, find_packages
import os

_globals = {}
version_file = "BrowserWrapper/version.py"
with open(version_file, "r") as f:
    exec(f.read().strip(), _globals)

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="BrowserWrapper", # Replace with your own username
    version=_globals["__version__"],
    author="Michael Fessenden",
    author_email="MikeFez@gmail.com",
    description="A selenium driver wrapper simplifying interactions with page elements",
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/MikeFez/BrowserWrapper",
    packages=[
        "BrowserWrapper"
    ],
    install_requires=[
        "selenium==3.141.0",
        "webdriver-manager==2.3.0"
    ],
    test_suite="test",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)