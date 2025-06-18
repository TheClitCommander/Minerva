from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="Minerva",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An advanced AI assistant that integrates multiple AI frameworks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Minerva",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "Minerva=Minerva.minerva_main:main",
            "Minerva-cli=Minerva.minerva_cli:cli",
        ],
    },
)
