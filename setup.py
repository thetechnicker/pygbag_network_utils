from setuptools import setup, find_packages
from pygbag_network_utils import VERSION

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="pygbag_network_utils",
    version=VERSION,
    packages=find_packages(),
    install_requires=requirements,
    url="https://github.com/thetechnicker/pygbag-multiplayer-sandbox",
    license="MIT",
    author="thetechnicker",
    author_email="106349149+thetechnicker@users.noreply.github.com",
    description="A Python library that provides network utilities for use with pygbag.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
