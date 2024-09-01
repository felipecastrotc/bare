# setup.py

from setuptools import setup, find_packages

setup(
    name="bare",
    version="0.1.0",
    description="BARE: Backup And Replication with Encryption",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Felipe C. T. Carvalho",
    author_email="bare@felipecastrotc.com",
    url="https://github.com/felipecastrotc/bare",  # Update with your URL
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "bare=bare.bare_main:main",  # 'bare' is the command name, 'bare.bare:main' is the reference to the script
        ],
    },
)
