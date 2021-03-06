import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="browser-wrapper-MikeFez", # Replace with your own username
    version="0.0.1",
    author="Michael Fessenden",
    author_email="MikeFez@gmail.com",
    description="A selenium driver wrapper simplifying interactions with page elements",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MikeFez/BrowserWrapper",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)