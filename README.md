# 🥖 Panadería Susan

## Descripción del proyecto

Panadería Susan es una aplicación web desarrollada para facilitar la gestión de una panadería artesanal mediante una plataforma digital. Su objetivo es ofrecer a los clientes una forma sencilla de consultar productos, agregarlos al carrito de compras y realizar pedidos en línea.

Asimismo, el sistema cuenta con un módulo administrativo que permite gestionar productos, consultar clientes y dar seguimiento a los pedidos realizados.

Este proyecto fue desarrollado como parte de la materia de **Arquitectura Orientada a Servicios (SOA)**.

## Objetivo general

Desarrollar una aplicación web para la gestión de una panadería artesanal que permita administrar el catálogo de productos, gestionar pedidos y facilitar la interacción entre los clientes y el personal administrativo, utilizando tecnologías de desarrollo web y contenedores Docker.

## Tecnologías utilizadas

| Tecnología | Descripción |
|---|---|
| Python 3.12 | Lenguaje de programación utilizado para el desarrollo del sistema. |
| Flask | Framework utilizado para desarrollar la aplicación web. |
| MySQL 8.4 | Sistema gestor de bases de datos. |
| PyMySQL | Biblioteca para conectar Python con MySQL. |
| HTML5 | Estructura de las páginas web. |
| CSS3 | Diseño y presentación de la interfaz. |
| Docker | Herramienta para crear y ejecutar contenedores. |
| Docker Compose | Herramienta para administrar los servicios de la aplicación. |
| ReportLab | Biblioteca para generar comprobantes en formato PDF. |

## Funcionalidades del sistema

### Módulo de clientes

- Registro de nuevos usuarios.
- Inicio y cierre de sesión.
- Consulta del catálogo de productos.
- Visualización de productos por categorías.
- Administración del carrito de compras.
- Selección de cantidades de productos.
- Realización de pedidos.
- Selección del método de pago.
- Registro del lugar y fecha de entrega.
- Confirmación de pedidos.
- Generación de comprobantes en PDF.
- Envío de comprobantes por correo electrónico.

### Módulo administrativo

- Inicio de sesión de administrador.
- Acceso al panel administrativo.
- Registro de nuevos productos.
- Consulta del catálogo de productos.
- Edición de información de productos.
- Eliminación de productos.
- Administración de categorías.
- Control de disponibilidad de productos.
- Consulta de clientes registrados.
- Consulta y gestión de pedidos.
- Actualización del estado de los pedidos.

## Estructura del proyecto

```text
Panaderia_Susan/
│
├── Templates/
│   ├── admin_clientes.html
│   ├── admin_dashboard.html
│   ├── admin_detalle_cliente.html
│   ├── admin_detalle_pedido.html
│   ├── admin_pedidos.html
│   ├── admin_producto_form.html
│   ├── admin_productos.html
│   ├── base.html
│   ├── carrito.html
│   ├── catalogo.html
│   ├── contacto.html
│   ├── index.html
│   ├── login.html
│   ├── login_admin.html
│   ├── pedido_confirmado.html
│   ├── realizar_pedido.html
│   ├── registro.html
│   └── seleccionar_acceso.html
│
├── database/
│   └── init.sql
│
├── static/
│   ├── img/
│   │   └── productos/
│   ├── panaderia.jpeg
│   └── styles.css
│
├── .dockerignore
├── .env.example
├── .gitignore
├── app.py
├── compose.yaml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Requisitos previos

Para ejecutar el proyecto se requiere:

- Docker Desktop instalado.
- Docker Compose disponible.
- Git instalado para clonar el repositorio.
- Navegador web actualizado.

## Instalación y ejecución del proyecto

### 1. Clonar el repositorio

Abrir una terminal y ejecutar:

```bash
git clone https://github.com/Michelle2160/Panaderia_Susan.git
```

### 2. Acceder a la carpeta del proyecto

```bash
cd Panaderia_Susan
```

### 3. Configurar las variables de entorno

Crear el archivo `.env` a partir de la plantilla `.env.example`.

En PowerShell ejecutar:

```powershell
Copy-Item .env.example .env
```

Abrir el archivo `.env` y configurar los valores correspondientes a:

- Contraseña de MySQL.
- Nombre de la base de datos.
- Usuario de MySQL.
- Contraseña del usuario de MySQL.
- Clave secreta de Flask.
- Configuración del servidor SMTP para el envío de correos.

**Importante:** No compartir ni subir el archivo `.env` a GitHub, debido a que contiene información confidencial.

### 4. Construir e iniciar los contenedores

Ejecutar el siguiente comando:

```bash
docker compose up --build -d
```

Este comando construye la imagen de la aplicación e inicia los servicios definidos en `compose.yaml`.

### 5. Verificar los contenedores

Para comprobar que los servicios estén funcionando correctamente:

```bash
docker compose ps
```

### 6. Consultar los registros de ejecución

Para visualizar los registros de los servicios:

```bash
docker compose logs -f
```

### 7. Acceder a la aplicación web

Abrir el navegador y entrar a la siguiente dirección:

**http://localhost:5000**

## Comandos útiles de Docker

| Comando | Función |
|---|---|
| `docker compose up -d` | Inicia los servicios en segundo plano. |
| `docker compose up --build -d` | Construye las imágenes e inicia los servicios. |
| `docker compose down` | Detiene y elimina los contenedores de la aplicación. |
| `docker compose ps` | Muestra el estado de los contenedores. |
| `docker compose logs -f` | Muestra los registros de ejecución. |
| `docker compose restart` | Reinicia los servicios. |

**Nota:** `docker compose down` no elimina por defecto los volúmenes persistentes de la base de datos. Para conservar los datos, evita utilizar la opción `-v`.

## Base de datos

El sistema utiliza **MySQL 8.4** como sistema gestor de bases de datos.

La estructura inicial se encuentra definida en el archivo:

`database/init.sql`

Este archivo contiene las instrucciones SQL para crear las tablas necesarias para el funcionamiento del sistema, entre ellas:

- `usuarios`
- `productos`
- `pedidos`
- `detalle_pedido`

Docker utiliza el script de inicialización cuando se crea por primera vez el volumen de datos de MySQL. Si el volumen ya existe, los cambios posteriores en `init.sql` no se aplican automáticamente.

## Seguridad y configuración

Para proteger la información del proyecto se implementaron las siguientes medidas:

- Uso de variables de entorno para almacenar credenciales.
- Exclusión del archivo `.env` mediante `.gitignore`.
- Exclusión de archivos innecesarios mediante `.dockerignore`.
- Uso de `.env.example` como plantilla de configuración.
- Separación de los servicios de aplicación y base de datos mediante Docker Compose.

No se deben publicar contraseñas, claves secretas ni credenciales de correo electrónico en el repositorio.

## Arquitectura de despliegue

El proyecto utiliza Docker Compose para ejecutar dos servicios principales:

**1. Servicio web**

Contiene la aplicación desarrollada con Python y Flask. Se encarga de atender las solicitudes de los usuarios y gestionar las funcionalidades del sistema.

**2. Servicio de base de datos**

Utiliza MySQL 8.4 para almacenar la información de usuarios, productos y pedidos.

Ambos servicios se comunican mediante la red interna administrada por Docker Compose.

## Autora

Proyecto académico desarrollado para la materia de Arquitectura Orientada a Servicios (SOA).

**Repositorio de GitHub:**

https://github.com/Michelle2160/Panaderia_Susan

---

**Panadería Susan – El sabor de lo tradicional, cada día.**
