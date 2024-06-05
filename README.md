<h1 align="center">Medical Clinic App</h1>

<h3 align="center">Summary</h3>
<p align="center">
    <img src="https://img.shields.io/badge/Python_versions-^3.11-green" alt="Python Versions">
    <img src="https://img.shields.io/badge/License-Apache_2.0-green" alt="License">
    <img src="https://img.shields.io/badge/style-ruff-rgb(208, 90, 16)" alt="Style">
    <img src="https://img.shields.io/badge/linter-ruff-black" alt="Linter">
</p>

<h3 align="center">Other</h3>
<p align="center">
    <img src="https://img.shields.io/badge/Develop_on-Arch_Linux-blue" alt="Develop on Arch Linux">
    <img src="https://img.shields.io/badge/Developers-1-red" alt="Developers count">
</p>

# Table of Contents

- [Table of Contents](#table-of-contents)
- [Overwriew](#overwriew)
- [Add csv files](#add-csv-files)
- [Tests](#tests)
- [Run app](#run-app)


# Overwriew

This is an app for interact with clients of medical clinic.

# Add csv files

Csv files should named by names by the names listed in the file `clinic_app/shared/__init__.py`.

Add symbol link to csv files into `src_csvs/` directory or create csv files manually

# Tests
If you want to test the application, you can create a docker image and run the application in a container using the following commands:

0. Change dir to root repository directory
1. docker build -t testing_medical_app:latest .
2. docker run --rm --name test-app testing_medical_app:latest
   
If you want to test and update code in real-time add this parameter to `docker run` command: `-v .:/app`

# Run app

1. Move the csv files according to the names in the file `clinic_app/shared/__init__.py`

2. Rename .env-example to .env and fill it file

3. Run locally by this commands:

```bash
poetry install --no-root
poetry run python clinic_app/frontend/telegram_bot/main.py
```

4. Or run in docker (prod mode) by this commands:
   
```bash
docker-compose up
```
