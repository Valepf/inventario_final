# 📦 Sistema de Gestión de Inventario

Aplicación web para la administración y control de inventario, desarrollada con **Python, Flask y MySQL**, con una interfaz web construida en **HTML, CSS y JavaScript**.

El sistema permite centralizar la gestión de productos, categorías, proveedores, órdenes, usuarios y reportes, incorporando autenticación y distintos niveles de acceso.

---

## 🚀 Funcionalidades principales

* Gestión de productos.
* Administración de categorías.
* Gestión de proveedores.
* Registro y seguimiento de órdenes.
* Control de usuarios.
* Roles de usuario y administrador.
* Autenticación mediante JWT.
* Dashboard de gestión.
* Reportes de inventario.
* Exportación de información a PDF.
* Control de relaciones entre productos, categorías y proveedores.
* Manejo de variables de entorno para configuración sensible.

---

## 🛠️ Tecnologías utilizadas

### Backend

* Python
* Flask
* Flask-JWT-Extended
* Flask-CORS
* Flask-SQLAlchemy
* Werkzeug

### Base de datos

* MySQL
* PyMySQL
* MySQL Connector

### Frontend

* HTML5
* CSS3
* JavaScript

### Otras herramientas

* python-dotenv
* xhtml2pdf
* Git
* GitHub

---

## 🔐 Autenticación y seguridad

El sistema cuenta con autenticación mediante **JSON Web Tokens (JWT)**.

Las contraseñas de los nuevos usuarios se almacenan utilizando hashing con **scrypt** mediante Werkzeug.

También se mantiene compatibilidad con usuarios creados durante etapas anteriores del desarrollo del proyecto.

Los datos sensibles y configuraciones locales se administran mediante variables de entorno y no se incluyen en el repositorio.

---

## 👥 Roles

### Administrador

Cuenta con acceso a las funciones administrativas del sistema, incluyendo gestión de:

* Productos
* Categorías
* Proveedores
* Usuarios
* Reportes

### Usuario

Dispone de acceso limitado a las funciones correspondientes a su rol dentro del sistema.

---

## 📁 Estructura del proyecto

```text
inventario_final/
│
├── backend/
│   ├── api/
│   │   ├── db/
│   │   ├── models/
│   │   ├── routes/
│   │   └── utils/
│   │
│   ├── static/
│   ├── templates/
│   ├── main.py
│   ├── requirements.txt
│   └── .gitignore
│
└── README.md
```

---

## ⚙️ Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Valepf/inventario_final.git
```

Ingresar al proyecto:

```bash
cd inventario_final/backend
```

### 2. Crear un entorno virtual

En Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

En Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la base de datos

El proyecto utiliza **MySQL**.

La conexión debe configurarse mediante las variables de entorno correspondientes antes de iniciar la aplicación.

---

## ▶️ Ejecutar el proyecto

Desde la carpeta `backend`:

```bash
python main.py
```

Por defecto, la aplicación se ejecuta en:

```text
http://localhost:5000
```

---

## 🎯 Objetivo del proyecto

Este proyecto fue desarrollado para aplicar conceptos de desarrollo web y backend en un sistema de gestión completo, incluyendo:

* Diseño de una aplicación modular.
* Desarrollo de APIs.
* Persistencia de datos.
* Autenticación y autorización.
* Gestión de roles.
* Implementación de reglas de negocio.
* Manejo de relaciones entre entidades.
* Generación de reportes.

---

## 📌 Estado

Proyecto funcional en proceso de mejora y documentación para portfolio.

---

## 👩‍💻 Autor

**Valepf**

GitHub: `github.com/Valepf`
