# 🏆 Torneo de Fútbol - App con Streamlit

Proyecto personal para crear una web tipo Promiedos para gestionar un torneo de fútbol amateur/local.

---

# 🧠 Objetivo

Construir una aplicación web simple pero escalable que permita:

- Tabla de posiciones
- Resultados de partidos
- Goleadores
- Panel admin básico para cargar datos

---

# 🛠️ Tecnologías usadas

- Python 🐍
- Streamlit 🌐
- SQLite 🗄️
- Git + GitHub 🔧

---

# 🚀 Cómo ejecutar el proyecto

## 1. Entrar a la carpeta del proyecto

cd torneo-futbol

## 2. Activar entorno virtual

source venv/bin/activate

## 3. Instalar dependencias

pip install streamlit

## 4. Ejecutar la app

streamlit run app.py

---

# 📁 Estructura del proyecto (actual)

torneo-futbol/
│
├── app.py
├── venv/
├── .gitignore
├── README.md

---

# 🧠 Problemas encontrados y soluciones

## ❌ Streamlit no encontrado
Error:
streamlit: command not found

✔ Solución:
source venv/bin/activate
pip install streamlit

---

## ❌ VS Code no abría carpeta correctamente
✔ Solución:
code .

---

## ❌ Git no reconocía main
Error:
src refspec main does not match any

✔ Solución:
git add .
git commit -m "init"
git branch -M main

---

## ❌ venv aparecía en Git
✔ Solución:

Crear archivo .gitignore con:

venv/
__pycache__/
*.pyc
*.db

---

## ❌ Git commit sin identidad
Error:
Author identity unknown

✔ Solución:
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"

---

## ❌ VS Code sandbox error
Error:
Permission denied (sandbox)

✔ Solución:
code --no-sandbox

---

## ❌ Streamlit no corría
Error:
streamlit: command not found

✔ Solución:
source venv/bin/activate

---

# 📌 Estado actual

- Python instalado ✔️
- Streamlit funcionando ✔️
- Git inicializado ✔️
- Proyecto base creado ✔️
- README documentado ✔️

---

# 🚀 Próximos pasos

- Crear base de datos SQLite
- Tabla de posiciones real
- Sistema de partidos
- Goleadores
- Panel admin
- Subir proyecto a GitHub

---

# 💡 Nota personal

Este proyecto es parte de un proceso de aprendizaje práctico:

Aprender construyendo, no solo estudiando teoría.