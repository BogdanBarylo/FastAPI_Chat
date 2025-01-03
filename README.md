[![Chat CI/CD](https://github.com/BogdanBarylo/FastAPI_Chat/actions/workflows/main.yml/badge.svg)](https://github.com/BogdanBarylo/FastAPI_Chat/actions/workflows/main.yml)

# FastAPI Chat

A simple chat application built using FastAPI. This project demonstrates the use of FastAPI to create a real-time chat application with basic functionalities.

## Features

- Real-time messaging using WebSockets.
- A lightweight and fast API for handling chat interactions.
- Easy setup and integration for future expansion.

## Requirements

- Python 3.7+
- FastAPI
- Uvicorn (ASGI server)
- Other dependencies listed in `pyproject.toml`.

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/BogdanBarylo/FastAPI_Chat.git
   cd FastAPI_Chat

2. Install the dependencies:

   ```bash
   make install

## Running the Application

1. To run the application in development mode:

    ```bash
    make dev
2. This will start the Redis server (if not already running) and launch the FastAPI server.

You can now access the application at ```bash http://localhost:8000.

## Usage
Open http://localhost:8000/docs for interactive API documentation powered by FastAPI.
The chat service can be accessed and interacted with via WebSockets.