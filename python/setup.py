from setuptools import setup, find_packages

setup(
    name="jbllmvm",
    version="1.0.0",
    description="A command-line tool for managing Google Cloud Platform virtual machines for running Large Language Models (LLMs) with Ollama",
    author="JetBrains",
    author_email="info@jetbrains.com",
    url="https://github.com/jetbrains/jbllmvm",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "paramiko",
        "requests",
        "google-auth",
        "google-api-python-client",
        "tomli; python_version < '3.11'",
    ],
    entry_points={
        "console_scripts": [
            "jbllmvm=jbllmvm.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)