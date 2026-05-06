from setuptools import setup, find_packages

setup(
    name="dscr-tools",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.4.0",
        "numpy>=1.21.0",
    ],
)
