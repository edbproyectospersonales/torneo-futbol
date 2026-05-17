# ⚽ Torneo Local — App Web con Streamlit + SQLite + Docker

---

## 📁 Estructura del proyecto

```
torneo_app/
├── app.py              → Interfaz principal (páginas y navegación)
├── database.py         → Conexión a SQLite y creación de tablas
├── queries.py          → Todas las consultas SQL
├── requirements.txt    → Dependencias Python
├── Dockerfile          → Cómo construir la imagen Docker
├── docker-compose.yml  → Cómo correr el contenedor
├── .dockerignore       → Archivos que Docker NO copia
├── data/               → Carpeta donde vive torneo.db (creada automáticamente)
└── README.md           → Este archivo
```

---

## 🐳 Correr con Docker (recomendado)

### Requisito único: instalar Docker Desktop
https://www.docker.com/products/docker-desktop

Una sola instalación, nunca más tocás Python ni pip directamente.

### Comandos

```bash
# 1. Entrar a la carpeta del proyecto
cd torneo_app

# 2. Construir y arrancar (la primera vez tarda ~1 min)
docker compose up --build

# 3. Abrir en el browser
# http://localhost:8501
```

```bash
# Parar la app
docker compose down

# Volver a arrancar (sin rebuild, es instantáneo)
docker compose up

# Ver los logs si algo falla
docker compose logs -f
```

### ¿Dónde se guardan los datos?
En la carpeta `data/torneo.db` de tu proyecto (fuera del contenedor).
Si borrás y volvés a crear el contenedor, los datos siguen ahí.

---

## 💻 Correr sin Docker (opcional)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
# → http://localhost:8501
```

---

## 🌐 Deploy gratuito

### Streamlit Community Cloud
1. Subí el proyecto a GitHub (sin la carpeta `data/`)
2. Entrá a https://share.streamlit.io
3. Conectá el repo → deploy automático

> Para deploy con datos persistentes, migrá luego a Railway.app o Render.com

---

## 💡 Ideas para expandir

- [ ] Contraseña en el panel admin (`st.secrets`)
- [ ] Fixture de próximos partidos
- [ ] Estadísticas por jugador (asistencias, tarjetas)
- [ ] Múltiples torneos / temporadas
- [ ] Migrar a PostgreSQL para deploy profesional
