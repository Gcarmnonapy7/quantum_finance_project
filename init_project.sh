#!/bin/bash

#init docker compose 

if [ ! -f .env ]; then
    echo "Creating .env file from .env.example"
    cp .env.example .env
fi

