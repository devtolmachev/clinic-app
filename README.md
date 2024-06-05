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
- [Run app](#run-app)


# Overwriew

This is an app for interact with clients of medical clinic.

# Run app

1. Move the csv files according to the names in the file `clinic_app/shared/__init__.py`

2. Rename .env-example to .env and fill it file

3. Run this commands
```bash
poetry install --no-root
poetry run python clinic_app/frontend/telegram_bot/main.py
```

