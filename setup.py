from setuptools import setup, find_packages

setup(
    name="bare",
    version="0.1.0",
    description="BARE: Backup And Replication with Encryption",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Felipe C. T. Carvalho",
    author_email="bare@felipecastrotc.com",
    url="https://github.com/felipecastrotc/bare",
    packages=find_packages(),
    install_requires=[
        "PyYAML>=5.4.1",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "bare=bare.bare_main:main",  # Ensure 'bare_main.py' exists within 'bare' package and defines 'main()'
        ],
    },
)