#!/bin/bash

echo "Creating the database"
python init_db.py

echo "Starting server"
python app.py
