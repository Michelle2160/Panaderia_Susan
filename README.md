\# 🥖 Panadería Susan



Aplicación web para la gestión de una panadería artesanal, desarrollada como proyecto académico de la materia de Arquitectura Orientada a Servicios (SOA).



El sistema permite consultar productos, registrarse, iniciar sesión, administrar un carrito de compras y realizar pedidos. También cuenta con un panel administrativo para gestionar productos, clientes y pedidos.



\## Tecnologías utilizadas



\- \*\*Python:\*\* lenguaje de programación.

\- \*\*Flask:\*\* framework para el desarrollo web.

\- \*\*MySQL 8.4:\*\* sistema gestor de base de datos.

\- \*\*PyMySQL:\*\* conexión entre Python y MySQL.

\- \*\*HTML5 y CSS3:\*\* estructura y diseño de la interfaz.

\- \*\*Docker:\*\* contenedorización de la aplicación.

\- \*\*Docker Compose:\*\* administración de los servicios.

\- \*\*ReportLab:\*\* generación de comprobantes PDF.



\## Funcionalidades principales



\### Clientes

\- Registro de usuarios.

\- Inicio y cierre de sesión.

\- Consulta del catálogo de productos.

\- Clasificación de productos por categorías.

\- Administración del carrito de compras.

\- Realización y confirmación de pedidos.

\- Selección del método de pago.

\- Generación y envío de comprobantes de pedido.



\### Administrador

\- Inicio de sesión administrativo.

\- Registro, consulta, edición y eliminación de productos.

\- Gestión de categorías y disponibilidad.

\- Consulta de clientes registrados.

\- Consulta y actualización de pedidos.



\## Estructura del proyecto



```text

Panaderia\_Susan/

│

├── Templates/

│   ├── base.html

│   ├── index.html

│   ├── catalogo.html

│   ├── carrito.html

│   └── ...

│

├── database/

│   └── init.sql

│

├── static/

│   ├── img/

│   └── styles.css

│

├── app.py

├── requirements.txt

├── Dockerfile

├── compose.yaml

├── .dockerignore

├── .gitignore

└── .env.example

```



\## Requisitos previos



Para ejecutar el proyecto se necesita:



\- Docker Desktop instalado.

\- Docker Compose disponible.

\- Git instalado (opcional, para clonar el repositorio).



\## Instalación y ejecución



\### 1. Clonar el repositorio



```bash

git clone https://github.com/Michelle2160/Panaderia\_Susan.git

```



\### 2. Entrar a la carpeta del proyecto



```bash

cd Panaderia\_Susan

```



\### 3. Configurar las variables de entorno



Crear el archivo `.env` a partir del archivo de ejemplo:



En PowerShell:



```powershell

Copy-Item .env.example .env

```



Editar el archivo `.env` y establecer las credenciales y variables necesarias para la aplicación y la base de datos.



No compartir ni subir el archivo `.env` a GitHub, ya que contiene información confidencial.



\### 4. Construir e iniciar los contenedores



```bash

docker compose up --build -d

```



\### 5. Consultar los registros de ejecución



```bash

docker compose logs -f

```



\### 6. Acceder a la aplicación



Abrir el navegador y visitar:



http://localhost:5000



\## Administración de Docker



Detener los servicios:



```bash

docker compose down

```



Iniciar los servicios nuevamente:



```bash

docker compose up -d

```



Consultar los contenedores:



```bash

docker compose ps

```



\## Base de datos



El proyecto utiliza MySQL 8.4. El archivo `database/init.sql` contiene la estructura inicial de las tablas necesarias para el funcionamiento del sistema.



\*\*Nota:\*\* Docker ejecuta los scripts de inicialización de MySQL al crear un volumen de datos nuevo. Si el volumen ya existe, modificar `init.sql` no actualiza automáticamente la base de datos existente.



\## Seguridad



\- Las credenciales se configuran mediante variables de entorno.

\- El archivo `.env` está excluido del repositorio mediante `.gitignore`.

\- El archivo `.env.example` proporciona una plantilla de configuración sin credenciales reales.



\## Autora



Proyecto académico desarrollado para la materia de Arquitectura Orientada a Servicios (SOA).



\*\*Repositorio:\*\* \[Panadería Susan en GitHub](https://github.com/Michelle2160/Panaderia\_Susan)

