FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

WORKDIR /home/vscode

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

