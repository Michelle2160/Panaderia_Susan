import os
import re
from decimal import Decimal
from functools import wraps
import pymysql
import ssl
import smtplib
import smtplib
import uuid
from werkzeug.utils import secure_filename
from io import BytesIO
from email.message import EmailMessage
from email.utils import formataddr
from xml.sax.saxutils import escape

from datetime import date
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from werkzeug.security import generate_password_hash, check_password_hash
from pymysql.cursors import DictCursor


# ==========================================
# CARGAR VARIABLES DEL ARCHIVO .ENV
# ==========================================

load_dotenv()


# ==========================================
# CONFIGURACIÓN DE FLASK
# ==========================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "clave-temporal-desarrollo"
)
# ==========================================
# CONFIGURACIÓN DE IMÁGENES DE PRODUCTOS
# ==========================================

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

CARPETA_PRODUCTOS = os.path.join(
    app.root_path,
    "static",
    "img",
    "productos"
)

os.makedirs(CARPETA_PRODUCTOS, exist_ok=True)

EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}


# ==========================================
# CONEXIÓN CON LA BASE DE DATOS MYSQL
# ==========================================

def obtener_conexion():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=DictCursor,
        charset="utf8mb4",
        connect_timeout=5
    )



# ==========================================
# CONTROL DE ACCESO POR ROL
# ==========================================

def requiere_rol(rol_requerido):

    def decorador(funcion):

        @wraps(funcion)
        def envoltura(*args, **kwargs):

            if "usuario_id" not in session:
                flash("Debes iniciar sesión para acceder.")
                return redirect(url_for("login"))

            if session.get("usuario_rol") != rol_requerido:
                flash("No tienes permisos para acceder a esta sección.")
                return redirect(url_for("inicio"))

            return funcion(*args, **kwargs)

        return envoltura

    return decorador


# ==========================================
# VALIDAR ACCESO ADMINISTRATIVO
# ==========================================

def es_administrador():

    return (
        "usuario_id" in session
        and session.get("usuario_rol") == "administrador"
    )


# ==========================================
# VALIDAR ACCESO ADMINISTRATIVO
# ==========================================

def es_administrador():
    return (
        "usuario_id" in session
        and session.get("usuario_rol") == "administrador"
    )


# ==========================================
# GENERAR VOUCHER PDF
# ==========================================

def generar_voucher_pdf(datos_pedido):
    """Genera el comprobante del pedido en memoria, sin guardarlo en disco."""
    archivo_pdf = BytesIO()

    documento = SimpleDocTemplate(
        archivo_pdf,
        pagesize=letter,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloPanaderia",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6b3e26"),
        fontSize=20,
        spaceAfter=4
    )
    estilo_subtitulo = ParagraphStyle(
        "SubtituloPanaderia",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#9b623e"),
        fontSize=10,
        spaceAfter=16
    )

    contenido = [
        Paragraph("PANADERÍA SUSAN", estilo_titulo),
        Paragraph("COMPROBANTE DE PEDIDO", estilo_subtitulo),
        Paragraph(
            f"<b>Folio:</b> {escape(str(datos_pedido['pedido_id']))}",
            estilos["Normal"]
        ),
        Paragraph(
            f"<b>Fecha del pedido:</b> {escape(str(datos_pedido['fecha_pedido']))}",
            estilos["Normal"]
        ),
        Spacer(1, 8),
        Paragraph(f"<b>Cliente:</b> {escape(datos_pedido['nombre'])}", estilos["Normal"]),
        Paragraph(f"<b>Correo:</b> {escape(datos_pedido['correo'])}", estilos["Normal"]),
        Paragraph(f"<b>Lugar de entrega:</b> {escape(datos_pedido['lugar_entrega'])}", estilos["Normal"]),
        Paragraph(f"<b>Fecha de entrega:</b> {escape(str(datos_pedido['fecha_entrega']))}", estilos["Normal"]),
        Spacer(1, 12)
    ]

    filas = [["Producto", "Cantidad", "Precio unitario", "Subtotal"]]
    for producto in datos_pedido["productos"]:
        filas.append([
            Paragraph(escape(str(producto["nombre"])), estilos["BodyText"]),
            str(producto["cantidad"]),
            f"${Decimal(str(producto['precio'])):.2f}",
            f"${Decimal(str(producto['subtotal'])):.2f}"
        ])

    tabla = Table(filas, colWidths=[75 * mm, 25 * mm, 35 * mm, 35 * mm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6b3e26")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8c4b2")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbf5ef")]),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 8)
    ]))
    contenido.extend([
        tabla,
        Spacer(1, 14),
        Paragraph(
            f"<b>Total del pedido: ${Decimal(str(datos_pedido['total'])):.2f}</b>",
            estilos["Heading2"]
        ),
        Paragraph(
            f"<b>Método de pago:</b> {escape(datos_pedido['metodo_pago'])}",
            estilos["Normal"]
        ),
        Paragraph("<b>Estado del pedido:</b> Pendiente", estilos["Normal"]),
        Paragraph("<b>Estado del pago:</b> Pendiente", estilos["Normal"]),
        Spacer(1, 20),
        Paragraph("Gracias por tu preferencia.", estilo_subtitulo)
    ])

    documento.build(contenido)
    archivo_pdf.seek(0)
    return archivo_pdf.getvalue()


# ==========================================
# ENVIAR VOUCHER POR CORREO
# ==========================================

def enviar_voucher_correo(destinatario, nombre_cliente, pedido_id, contenido_pdf):
    """Envía el PDF al correo registrado del cliente mediante SMTP."""

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_usuario = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    correo_remitente = os.getenv("SMTP_FROM", smtp_usuario or "")
 # Validar configuración
    if not all([smtp_host, smtp_usuario, smtp_password,
                correo_remitente, destinatario]):
        raise ValueError(
            "Falta configurar SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM o el correo del cliente."
        )

    mensaje = EmailMessage()
    mensaje["Subject"] = f"Comprobante de tu pedido #{pedido_id} - Panadería Susan"
    mensaje["From"] =  formataddr(
        ("Panadería Susan", correo_remitente)
    )
    mensaje["To"] = destinatario
    mensaje.set_content(
        f"Hola {nombre_cliente},\n\n"
        f"Gracias por comprar en Panadería Susan. Adjuntamos el comprobante PDF "
        f"de tu pedido número {pedido_id}.\n\n"
        "Conserva este archivo como referencia de tu compra.\n"
        "Panadería Susan"
    )
    mensaje.add_attachment(
        contenido_pdf,
        maintype="application",
        subtype="pdf",
        filename=f"voucher_pedido_{pedido_id}.pdf"
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as servidor:
        servidor.ehlo()
        servidor.starttls()
        servidor.ehlo()
        servidor.login(smtp_usuario, smtp_password)
        servidor.send_message(mensaje)


# ==========================================
# PÁGINA PRINCIPAL
# ==========================================

@app.route("/")
def inicio():
    return render_template("index.html")


# ==========================================
# SELECCIÓN DE TIPO DE ACCESO
# ==========================================

@app.route("/acceso")
def seleccionar_acceso():
    return render_template("seleccionar_acceso.html")


# ==========================================
# REGISTRO DE USUARIOS
# ==========================================

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "GET":
        return render_template("registro.html")

    nombre = request.form.get("nombre", "").strip()
    correo = request.form.get("correo", "").strip().lower()
    contrasena = request.form.get("contrasena", "")
    confirmar = request.form.get("confirmar_contrasena", "")
    acepta_terminos = request.form.get("acepta_terminos")

    # Validar campos obligatorios
    if not nombre or not correo or not contrasena:
        flash("Completa todos los campos obligatorios.")
        return redirect(url_for("registro"))

    # Validar nombre
    if len(nombre) < 3 or len(nombre) > 100:
        flash("El nombre debe tener entre 3 y 100 caracteres.")
        return redirect(url_for("registro"))

    # Validar correo electrónico
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        flash("Introduce un correo electrónico válido.")
        return redirect(url_for("registro"))

    if len(correo) > 150:
        flash("El correo electrónico es demasiado largo.")
        return redirect(url_for("registro"))

    # Validar contraseña
    if len(contrasena) < 8:
        flash("La contraseña debe tener al menos 8 caracteres.")
        return redirect(url_for("registro"))

    if contrasena != confirmar:
        flash("Las contraseñas no coinciden.")
        return redirect(url_for("registro"))

    if not acepta_terminos:
        flash("Debes aceptar los términos y condiciones.")
        return redirect(url_for("registro"))

    contrasena_hash = generate_password_hash(contrasena)
    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO usuarios
                    (nombre, correo, contrasena_hash, rol)
                VALUES (%s, %s, %s, %s)
                """,
                (nombre, correo, contrasena_hash, "cliente")
            )

        conexion.commit()

        flash("Tu cuenta se creó correctamente. Ya puedes iniciar sesión.")
        return redirect(url_for("login"))

    except pymysql.err.IntegrityError:
        if conexion:
            conexion.rollback()

        flash("Este correo ya está registrado.")
        return redirect(url_for("registro"))

    except pymysql.MySQLError:
        if conexion:
            conexion.rollback()

        app.logger.exception("Error al registrar el usuario")
        flash("No fue posible completar el registro. Inténtalo más tarde.")
        return redirect(url_for("registro"))

    finally:
        if conexion:
            conexion.close()


# ==========================================
# INICIO DE SESIÓN DEL CLIENTE
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    correo = request.form.get("correo", "").strip().lower()
    contrasena = request.form.get("contrasena", "")

    # Validar campos obligatorios
    if not correo or not contrasena:
        flash("Introduce tu correo y contraseña.")
        return redirect(url_for("login"))

    # Validar formato del correo
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        flash("Introduce un correo electrónico válido.")
        return redirect(url_for("login"))

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nombre, correo, contrasena_hash, rol
                FROM usuarios
                WHERE correo = %s
                """,
                (correo,)
            )

            usuario = cursor.fetchone()

        if usuario and check_password_hash(
            usuario["contrasena_hash"],
            contrasena
        ):

            # Evitar que un administrador ingrese como cliente
            if usuario["rol"] != "cliente":
                flash("Esta cuenta debe ingresar por el acceso administrativo.")
                return redirect(url_for("login"))

            # Guardar sesión del cliente
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nombre"] = usuario["nombre"]
            session["rol"] = usuario["rol"]

            flash("¡Bienvenido a Panadería Susan!")
            return redirect(url_for("inicio"))

        flash("El correo o la contraseña son incorrectos.")
        return redirect(url_for("login"))

    except pymysql.MySQLError:
        app.logger.exception("Error al iniciar sesión del cliente")
        flash("No fue posible iniciar sesión. Inténtalo más tarde.")
        return redirect(url_for("login"))

    finally:
        if conexion:
            conexion.close()


# ==========================================
# INICIO DE SESIÓN DEL ADMINISTRADOR
# ==========================================

@app.route("/admin/login", methods=["GET", "POST"])
def login_admin():

    # Mostrar formulario de inicio de sesión
    if request.method == "GET":
        return render_template("login_admin.html")

    correo = request.form.get("correo", "").strip().lower()
    contrasena = request.form.get("contrasena", "")

    # Validar campos obligatorios
    if not correo or not contrasena:
        flash("Introduce tu correo y contraseña.")
        return redirect(url_for("login_admin"))

    # Validar formato del correo
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        flash("Introduce un correo electrónico válido.")
        return redirect(url_for("login_admin"))

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nombre, correo, contrasena_hash, rol
                FROM usuarios
                WHERE correo = %s
                """,
                (correo,)
            )

            usuario = cursor.fetchone()

        if usuario and check_password_hash(
            usuario["contrasena_hash"],
            contrasena
        ):

            # Verificar que la cuenta sea administrador
            if usuario["rol"] != "admin":
                flash("No tienes permisos de administrador.")
                return redirect(url_for("login_admin"))

            # Guardar sesión administrativa
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nombre"] = usuario["nombre"]
            # Unificar el rol para todas las rutas administrativas
            session["usuario_rol"] = "administrador"
            # Mantener compatibilidad con las funciones existentes
            session["rol"] = usuario["rol"]

            flash("Bienvenido al panel administrativo.")

            return redirect(url_for("admin_dashboard"))

        flash("El correo o la contraseña son incorrectos.")
        return redirect(url_for("login_admin"))

    except pymysql.MySQLError:
        app.logger.exception("Error al iniciar sesión del administrador")
        flash("No fue posible iniciar sesión. Inténtalo más tarde.")
        return redirect(url_for("login_admin"))

    finally:
        if conexion:
            conexion.close()



# ==========================================
# PANEL ADMINISTRATIVO
# ==========================================

@app.route("/admin")
def admin_dashboard():

    if "usuario_id" not in session or session.get("rol") != "admin":
        flash("Debes iniciar sesión como administrador.")
        return redirect(url_for("login_admin"))

    return render_template("admin_dashboard.html")



# GESTIÓN DE PRODUCTOS
# ==========================================
@app.route("/admin/productos")
@requiere_rol("administrador")
def admin_productos():

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nombre, descripcion, precio,
                       imagen, disponible, categoria
                FROM productos
                ORDER BY fecha_creacion DESC
                """
            )

            productos = cursor.fetchall()

        return render_template(
            "admin_productos.html",
            productos=productos
        )

    except pymysql.MySQLError:
        app.logger.exception("Error al consultar productos")
        flash("No fue posible cargar los productos.")
        return redirect(url_for("admin_dashboard"))

    finally:
        if conexion:
            conexion.close()

# ==========================================
# AGREGAR PRODUCTO
# ==========================================

@app.route("/admin/productos/nuevo", methods=["GET", "POST"])
def admin_nuevo_producto():

    if not es_administrador():
        flash("Debes iniciar sesión como administrador.")
        return redirect(url_for("login_admin"))

    if request.method == "GET":
        return render_template("admin_producto_form.html")

    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    precio_texto = request.form.get("precio", "").strip()
    categoria = request.form.get("categoria", "").strip()

    imagen = request.files.get("imagen")

    # Validar campos obligatorios
    if not nombre or not precio_texto or not categoria:
        flash("Completa los campos obligatorios.")
        return redirect(url_for("admin_nuevo_producto"))

    # Validar longitud del nombre
    if len(nombre) > 100:
        flash("El nombre no puede superar los 100 caracteres.")
        return redirect(url_for("admin_nuevo_producto"))

    # Validar categorías permitidas
    categorias_permitidas = [
        "Especialidad de la casa",
        "Pan dulce",
        "Pan blanco",
        "Bajo pedido"
    ]

    if categoria not in categorias_permitidas:
        flash("Selecciona una categoría válida.")
        return redirect(url_for("admin_nuevo_producto"))

    # Validar precio
    try:
        precio = Decimal(precio_texto)

        if not precio.is_finite() or precio <= 0:
            raise ValueError

    except (ValueError, TypeError, ArithmeticError):
        flash("Introduce un precio válido mayor que cero.")
        return redirect(url_for("admin_nuevo_producto"))

    # Procesar imagen
    nombre_imagen = None

    if imagen and imagen.filename:

        nombre_original = secure_filename(imagen.filename)

        if "." not in nombre_original:
            flash("El archivo de imagen no tiene una extensión válida.")
            return redirect(url_for("admin_nuevo_producto"))

        extension = nombre_original.rsplit(".", 1)[1].lower()

        if extension not in EXTENSIONES_PERMITIDAS:
            flash("Formato de imagen no permitido.")
            return redirect(url_for("admin_nuevo_producto"))

        nombre_imagen = f"{uuid.uuid4().hex}.{extension}"

        ruta_imagen = os.path.join(
            CARPETA_PRODUCTOS,
            nombre_imagen
        )

        imagen.save(ruta_imagen)

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO productos
                    (nombre, descripcion, precio, imagen,
                     disponible, categoria)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    nombre,
                    descripcion,
                    precio,
                    f"img/productos/{nombre_imagen}" if nombre_imagen else None,
                    1,
                    categoria
                )
            )

        conexion.commit()

        flash("El producto se registró correctamente.")
        return redirect(url_for("admin_productos"))

    except pymysql.MySQLError:
        if conexion:
            conexion.rollback()

        app.logger.exception("Error al registrar producto")
        flash("No fue posible registrar el producto.")
        return redirect(url_for("admin_nuevo_producto"))

    finally:
        if conexion:
            conexion.close()

# ==========================================
# CERRAR SESIÓN
# ==========================================

@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for("seleccionar_acceso"))

# ==========================================
# CATÁLOGO DE PRODUCTOS
# ==========================================

@app.route("/catalogo")
def catalogo():

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nombre, descripcion, precio, imagen, categoria
                FROM productos
                WHERE disponible = TRUE
                ORDER BY categoria, nombre
                """
            )

            productos = cursor.fetchall()

        return render_template(
            "catalogo.html",
            productos=productos
        )

    except pymysql.MySQLError:
        app.logger.exception("Error al cargar el catálogo")
        return "No fue posible cargar los productos.", 500

    finally:
        if conexion:
            conexion.close()

# ==========================================
# AGREGAR PRODUCTOS AL CARRITO
# ==========================================


@app.route("/agregar-carrito/<int:producto_id>", methods=["POST"])
def agregar_carrito(producto_id):

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nombre
                FROM productos
                WHERE id = %s AND disponible = TRUE
                """,
                (producto_id,)
            )

            producto = cursor.fetchone()

        if not producto:
            flash("El producto no está disponible.")
            return redirect(url_for("catalogo"))

        carrito = session.get("carrito", {})
        clave = str(producto_id)
        carrito[clave] = int(carrito.get(clave, 0)) + 1
        session["carrito"] = carrito

        flash(f"{producto['nombre']} se agregó al carrito.")
        return redirect(url_for("catalogo"))

    except pymysql.MySQLError:
        app.logger.exception("Error al agregar producto al carrito")
        flash("No fue posible agregar el producto.")
        return redirect(url_for("catalogo"))

    finally:
        if conexion:
            conexion.close()


# ==========================================
# EDITAR PRODUCTO
# ==========================================

@app.route("/admin/productos/editar/<int:producto_id>", methods=["GET", "POST"])
def admin_editar_producto(producto_id):

    if not es_administrador():
        flash("Debes iniciar sesión como administrador.")
        return redirect(url_for("login_admin"))

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:

            cursor.execute(
                """
                SELECT id, nombre, descripcion, precio,
                       imagen, disponible, categoria
                FROM productos
                WHERE id = %s
                """,
                (producto_id,)
            )

            producto = cursor.fetchone()

            if not producto:
                flash("El producto no existe.")
                return redirect(url_for("admin_productos"))

            if request.method == "GET":
                return render_template(
                    "admin_producto_form.html",
                    producto=producto
                )

            nombre = request.form.get("nombre", "").strip()
            descripcion = request.form.get("descripcion", "").strip()
            precio_texto = request.form.get("precio", "").strip()
            categoria = request.form.get("categoria", "").strip()
            imagen = request.files.get("imagen")

            if not nombre or not precio_texto or not categoria:
                flash("Completa los campos obligatorios.")
                return redirect(url_for(
                    "admin_editar_producto",
                    producto_id=producto_id
                ))

            if len(nombre) > 100 or len(categoria) > 30:
                flash("El nombre o la categoría exceden la longitud permitida.")
                return redirect(url_for(
                    "admin_editar_producto",
                    producto_id=producto_id
                ))

            try:
                precio = Decimal(precio_texto)

                if not precio.is_finite() or precio <= 0:
                    raise ValueError

            except (ValueError, TypeError, ArithmeticError):
                flash("Introduce un precio válido mayor que cero.")
                return redirect(url_for(
                    "admin_editar_producto",
                    producto_id=producto_id
                ))

            ruta_imagen_bd = producto["imagen"]

            if imagen and imagen.filename:

                nombre_original = secure_filename(imagen.filename)

                if "." not in nombre_original:
                    flash("El archivo no tiene una extensión válida.")
                    return redirect(url_for(
                        "admin_editar_producto",
                        producto_id=producto_id
                    ))

                extension = nombre_original.rsplit(".", 1)[1].lower()

                if extension not in EXTENSIONES_PERMITIDAS:
                    flash("Formato de imagen no permitido.")
                    return redirect(url_for(
                        "admin_editar_producto",
                        producto_id=producto_id
                    ))

                nombre_imagen = f"{uuid.uuid4().hex}.{extension}"

                ruta_archivo = os.path.join(
                    CARPETA_PRODUCTOS,
                    nombre_imagen
                )

                imagen.save(ruta_archivo)

                ruta_imagen_bd = f"img/productos/{nombre_imagen}"

            cursor.execute(
                """
                UPDATE productos
                SET nombre = %s,
                    descripcion = %s,
                    precio = %s,
                    imagen = %s,
                    categoria = %s
                WHERE id = %s
                """,
                (
                    nombre,
                    descripcion,
                    precio,
                    ruta_imagen_bd,
                    categoria,
                    producto_id
                )
            )

        conexion.commit()

        flash("El producto se actualizó correctamente.")
        return redirect(url_for("admin_productos"))

    except pymysql.MySQLError:
        if conexion:
            conexion.rollback()

        app.logger.exception("Error al editar producto")
        flash("No fue posible actualizar el producto.")
        return redirect(url_for("admin_productos"))

    finally:
        if conexion:
            conexion.close()


# ==========================================
# DESACTIVAR PRODUCTO
# ==========================================

@app.route(
    "/admin/productos/desactivar/<int:producto_id>",
    methods=["POST"]
)
def admin_desactivar_producto(producto_id):

    if not es_administrador():
        flash("Debes iniciar sesión como administrador.")
        return redirect(url_for("login_admin"))

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:
            cursor.execute(
                """
                UPDATE productos
                SET disponible = 0
                WHERE id = %s
                """,
                (producto_id,)
            )

            if cursor.rowcount == 0:
                flash("No se encontró el producto.")
            else:
                flash("El producto se desactivó correctamente.")

        conexion.commit()

    except pymysql.MySQLError:
        if conexion:
            conexion.rollback()

        app.logger.exception("Error al desactivar producto")
        flash("No fue posible desactivar el producto.")

    finally:
        if conexion:
            conexion.close()

    return redirect(url_for("admin_productos"))


# ==========================================
# CONSULTAR CARRITO
# ==========================================

@app.route("/carrito")
def carrito():

    carrito_sesion = session.get("carrito", {})
    productos_carrito = []
    total = 0

    if not carrito_sesion:
        return render_template(
            "carrito.html",
            productos=[],
            total=0
        )

    conexion = None

    try:
        conexion = obtener_conexion()

        ids = [int(producto_id) for producto_id in carrito_sesion.keys()]
        marcadores = ",".join(["%s"] * len(ids))

        with conexion.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT id, nombre, precio, imagen
                FROM productos
                WHERE id IN ({marcadores})
                  AND disponible = TRUE
                """,
                tuple(ids)
            )

            productos = cursor.fetchall()

        for producto in productos:
            cantidad = int(carrito_sesion.get(str(producto["id"]), 0))

            if cantidad <= 0:
                continue

            subtotal = producto["precio"] * cantidad

            productos_carrito.append({
                "id": producto["id"],
                "nombre": producto["nombre"],
                "precio": producto["precio"],
                "imagen": producto["imagen"],
                "cantidad": cantidad,
                "subtotal": subtotal
            })

            total += subtotal

        return render_template(
            "carrito.html",
            productos=productos_carrito,
            total=total
        )

    except (pymysql.MySQLError, ValueError, TypeError):
        app.logger.exception("Error al consultar el carrito")
        return "No fue posible consultar el carrito.", 500

    finally:
        if conexion:
            conexion.close()


# ==========================================
# CONTADOR DE PRODUCTOS DEL CARRITO
# ==========================================

@app.context_processor
def contar_productos_carrito():

    carrito_sesion = session.get("carrito", {})

    cantidad_productos = sum(
        int(cantidad) for cantidad in carrito_sesion.values()
    )

    return {
        "cantidad_carrito": cantidad_productos
    }


# ==========================================
# REALIZAR PEDIDO
# ==========================================

@app.route("/realizar-pedido", methods=["GET", "POST"])
def realizar_pedido():

    if "usuario_id" not in session:
        flash("Debes iniciar sesión para realizar un pedido.")
        return redirect(url_for("login"))

    carrito_sesion = session.get("carrito", {})

    if not carrito_sesion:
        flash("Tu carrito está vacío.")
        return redirect(url_for("catalogo"))

    if request.method == "GET":
        return render_template(
            "realizar_pedido.html",
            fecha_minima=date.today().isoformat()
        )

    lugar_entrega = request.form.get("lugar_entrega", "").strip()
    fecha_entrega = request.form.get("fecha_entrega", "").strip()
    metodo_pago = request.form.get("metodo_pago", "").strip()

    if not lugar_entrega or len(lugar_entrega) > 255:
        flash("Ingresa un lugar de entrega válido.")
        return redirect(url_for("realizar_pedido"))

    if metodo_pago not in ("Efectivo", "Tarjeta"):
        flash("Selecciona un método de pago válido.")
        return redirect(url_for("realizar_pedido"))

    try:
        fecha_seleccionada = date.fromisoformat(fecha_entrega)
    except (ValueError, TypeError):
        flash("Selecciona una fecha de entrega válida.")
        return redirect(url_for("realizar_pedido"))

    if fecha_seleccionada < date.today():
        flash("La fecha de entrega no puede ser anterior a hoy.")
        return redirect(url_for("realizar_pedido"))

    # La tarjeta todavía no cuenta con validación de pago.
    if metodo_pago == "Tarjeta":
        flash(
            "La validación de tarjeta aún no está configurada. "
            "Selecciona efectivo."
        )
        return redirect(url_for("realizar_pedido"))

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:

            # Consultar datos del cliente.
            cursor.execute(
                """
                SELECT nombre, correo
                FROM usuarios
                WHERE id = %s
                """,
                (session["usuario_id"],)
            )

            usuario_pedido = cursor.fetchone()

        if not usuario_pedido or not usuario_pedido.get("correo"):
            flash(
                "No encontramos un correo electrónico asociado "
                "a tu cuenta."
            )
            return redirect(url_for("realizar_pedido"))

        ids_productos = [
            int(id_producto)
            for id_producto in carrito_sesion.keys()
        ]

        if not ids_productos:
            flash("Tu carrito está vacío.")
            return redirect(url_for("catalogo"))

        placeholders = ", ".join(["%s"] * len(ids_productos))

        with conexion.cursor() as cursor:

            # Consultar productos disponibles.
            cursor.execute(
                f"""
                SELECT id, nombre, precio
                FROM productos
                WHERE disponible = TRUE
                  AND id IN ({placeholders})
                """,
                tuple(ids_productos)
            )

            productos = cursor.fetchall()

            if len(productos) != len(set(ids_productos)):
                flash("Uno o más productos ya no están disponibles.")
                return redirect(url_for("carrito"))

            total = 0
            detalles = []
            productos_comprobante = []

            for producto in productos:

                cantidad = int(
                    carrito_sesion.get(str(producto["id"]), 0)
                )

                if cantidad <= 0:
                    raise ValueError(
                        "Cantidad de producto no válida."
                    )

                precio = producto["precio"]
                subtotal = precio * cantidad
                total += subtotal

                detalles.append((
                    producto["id"],
                    cantidad,
                    precio
                ))

                productos_comprobante.append({
                    "nombre": producto["nombre"],
                    "cantidad": cantidad,
                    "precio": precio,
                    "subtotal": subtotal
                })

            estado_pago = "Pendiente"

            # Registrar pedido.
            cursor.execute(
                """
                INSERT INTO pedidos
                    (usuario_id, total, metodo_pago, lugar_entrega,
                     fecha_entrega, estado, estado_pago)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session["usuario_id"],
                    total,
                    metodo_pago,
                    lugar_entrega,
                    fecha_entrega,
                    "Pendiente",
                    estado_pago
                )
            )

            pedido_id = cursor.lastrowid

            # Registrar productos del pedido.
            for producto_id, cantidad, precio in detalles:

                cursor.execute(
                    """
                    INSERT INTO detalle_pedido
                        (pedido_id, producto_id, cantidad, precio_unitario)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        pedido_id,
                        producto_id,
                        cantidad,
                        precio
                    )
                )

        # Guardar definitivamente el pedido.
        conexion.commit()

        # Cerrar conexión antes de enviar el correo.
        conexion.close()
        conexion = None

        # Generar y enviar comprobante.
        correo_enviado = False
        correo_cliente = usuario_pedido["correo"]

        datos_voucher = {
            "pedido_id": pedido_id,
            "fecha_pedido": date.today(),
            "nombre": usuario_pedido["nombre"],
            "correo": correo_cliente,
            "lugar_entrega": lugar_entrega,
            "fecha_entrega": fecha_entrega,
            "metodo_pago": metodo_pago,
            "total": total,
            "productos": productos_comprobante
        }

        try:
            contenido_pdf = generar_voucher_pdf(datos_voucher)

            enviar_voucher_correo(
                destinatario=correo_cliente,
                nombre_cliente=usuario_pedido["nombre"],
                pedido_id=pedido_id,
                contenido_pdf=contenido_pdf
            )

            correo_enviado = True

        except Exception:
            app.logger.exception(
                "El pedido %s se guardó, pero no fue posible enviar el voucher.",
                pedido_id
            )

        # Vaciar carrito después de guardar el pedido.
        session["carrito"] = {}

        return render_template(
            "pedido_confirmado.html",
            pedido_id=pedido_id,
            total=total,
            metodo_pago=metodo_pago,
            estado_pago=estado_pago,
            lugar_entrega=lugar_entrega,
            fecha_entrega=fecha_entrega,
            productos=productos_comprobante,
            fecha_pedido=date.today(),
            correo_cliente=correo_cliente,
            correo_enviado=correo_enviado
        )

    except (pymysql.MySQLError, ValueError, TypeError):

        if conexion:
            conexion.rollback()

        app.logger.exception("Error al registrar el pedido")

        flash(
            "No fue posible registrar tu pedido. "
            "Inténtalo nuevamente."
        )

        return redirect(url_for("carrito"))

    finally:

        if conexion:
            conexion.close()


# ==========================================
# GESTIÓN DE PEDIDOS
# ==========================================

@app.route("/admin/pedidos")
def admin_pedidos():

    if not es_administrador():
        flash("Debes iniciar sesión como administrador.")
        return redirect(url_for("login_admin"))

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT
                    p.id,
                    p.usuario_id,
                    u.nombre AS nombre_cliente,
                    u.correo AS correo_cliente,
                    p.total,
                    p.metodo_pago,
                    p.lugar_entrega,
                    p.fecha_entrega,
                    p.estado,
                    p.estado_pago,
                    p.fecha_pedido
                FROM pedidos AS p
                INNER JOIN usuarios AS u
                    ON p.usuario_id = u.id
                ORDER BY p.fecha_pedido DESC, p.id DESC
            """)

            pedidos = cursor.fetchall()

        return render_template(
            "admin_pedidos.html",
            pedidos=pedidos
        )

    except pymysql.MySQLError:
        app.logger.exception("Error al consultar pedidos")
        flash("No fue posible cargar los pedidos.")
        return redirect(url_for("admin_dashboard"))

    finally:
        if conexion:
            conexion.close()

# ==========================================
# DETALLE DE PEDIDO
# ==========================================

@app.route("/admin/pedidos/<int:pedido_id>")
def admin_detalle_pedido(pedido_id):

    if not es_administrador():
        flash("Debes iniciar sesión como administrador.")
        return redirect(url_for("login_admin"))

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:

            cursor.execute("""
                SELECT
                    p.*,
                    u.nombre AS nombre_cliente,
                    u.correo AS correo_cliente
                FROM pedidos AS p
                INNER JOIN usuarios AS u
                    ON p.usuario_id = u.id
                WHERE p.id = %s
            """, (pedido_id,))

            pedido = cursor.fetchone()

            if not pedido:
                flash("El pedido no existe.")
                return redirect(url_for("admin_pedidos"))

            cursor.execute("""
                SELECT
                    dp.producto_id,
                    pr.nombre AS nombre_producto,
                    dp.cantidad,
                    dp.precio_unitario,
                    (dp.cantidad * dp.precio_unitario) AS subtotal
                FROM detalle_pedido AS dp
                INNER JOIN productos AS pr
                    ON dp.producto_id = pr.id
                WHERE dp.pedido_id = %s
            """, (pedido_id,))

            detalles = cursor.fetchall()

        return render_template(
            "admin_detalle_pedido.html",
            pedido=pedido,
            detalles=detalles
        )

    except pymysql.MySQLError:
        app.logger.exception("Error al consultar el detalle del pedido")
        flash("No fue posible cargar el detalle del pedido.")
        return redirect(url_for("admin_pedidos"))

    finally:
        if conexion:
            conexion.close()
            
# ==========================================
# ACTUALIZAR ESTADO DEL PEDIDO
# ==========================================

@app.route(
    "/admin/pedidos/actualizar-estado/<int:pedido_id>",
    methods=["POST"]
)
def admin_actualizar_estado_pedido(pedido_id):

    if not es_administrador():
        flash("Debes iniciar sesión como administrador.")
        return redirect(url_for("login_admin"))

    estados_permitidos = [
        "Pendiente",
        "En preparación",
        "Listo para entregar",
        "Entregado"
    ]

    nuevo_estado = request.form.get("estado", "").strip()

    if nuevo_estado not in estados_permitidos:
        flash("El estado seleccionado no es válido.")
        return redirect(
            url_for("admin_detalle_pedido", pedido_id=pedido_id)
        )

    conexion = None

    try:
        conexion = obtener_conexion()

        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE pedidos
                SET estado = %s
                WHERE id = %s
            """, (nuevo_estado, pedido_id))

            if cursor.rowcount == 0:
                flash("No se encontró el pedido solicitado.")
                return redirect(url_for("admin_pedidos"))

        conexion.commit()

        flash("El estado del pedido se actualizó correctamente.")

    except pymysql.MySQLError:
        if conexion:
            conexion.rollback()

        app.logger.exception("Error al actualizar el estado del pedido")
        flash("No fue posible actualizar el estado del pedido.")

    finally:
        if conexion:
            conexion.close()

    return redirect(
        url_for("admin_detalle_pedido", pedido_id=pedido_id)
    )




# ==========================================
# DETALLE E HISTORIAL DE CLIENTE
# ==========================================
@app.route("/admin/clientes/<int:cliente_id>")
@requiere_rol("administrador")
def admin_detalle_cliente(cliente_id):

    conexion = obtener_conexion()

    try:
        with conexion.cursor() as cursor:

            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    correo,
                    fecha_registro
                FROM usuarios
                WHERE id = %s
                AND rol = 'cliente'
            """, (cliente_id,))

            cliente = cursor.fetchone()

            if cliente is None:
                flash("No se encontró el cliente solicitado.")
                return redirect(url_for("admin_clientes"))

            cursor.execute("""
                SELECT
                    id,
                    total,
                    metodo_pago,
                    lugar_entrega,
                    fecha_entrega,
                    estado,
                    estado_pago,
                    fecha_pedido
                FROM pedidos
                WHERE usuario_id = %s
                ORDER BY fecha_pedido DESC
            """, (cliente_id,))

            pedidos = cursor.fetchall()

    finally:
        conexion.close()

    total_pedidos = len(pedidos)

    total_compras = sum(
        (pedido["total"] for pedido in pedidos),
        Decimal("0.00")
    )

    return render_template(
        "admin_detalle_cliente.html",
        cliente=cliente,
        pedidos=pedidos,
        total_pedidos=total_pedidos,
        total_compras=total_compras
    )


# ==========================================
# GESTIÓN DE CLIENTES
# LISTADO Y BÚSQUEDA
# ==========================================

# ==========================================
# GESTIÓN DE CLIENTES
# LISTADO Y BÚSQUEDA
# ==========================================

@app.route("/admin/clientes")
@requiere_rol("administrador")
def admin_clientes():

    busqueda = request.args.get("busqueda", "").strip()

    conexion = obtener_conexion()

    try:
        with conexion.cursor() as cursor:

            consulta = """
                SELECT
                    u.id,
                    u.nombre,
                    u.correo,
                    u.fecha_registro,
                    COUNT(p.id) AS total_pedidos
                FROM usuarios u
                LEFT JOIN pedidos p
                    ON u.id = p.usuario_id
                WHERE u.rol = 'cliente'
            """

            parametros = []

            if busqueda:
                consulta += """
                    AND (
                        u.nombre LIKE %s
                        OR u.correo LIKE %s
                    )
                """

                parametros.extend([
                    f"%{busqueda}%",
                    f"%{busqueda}%"
                ])

            consulta += """
                GROUP BY
                    u.id,
                    u.nombre,
                    u.correo,
                    u.fecha_registro
                ORDER BY u.fecha_registro DESC
            """

            cursor.execute(consulta, parametros)
            clientes = cursor.fetchall()

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM usuarios
                WHERE rol = 'cliente'
            """)

            total_clientes = cursor.fetchone()["total"]

    finally:
        conexion.close()

    return render_template(
        "admin_clientes.html",
        clientes=clientes,
        busqueda=busqueda,
        total_clientes=total_clientes
    )
# ==========================================
# ELIMINAR CLIENTE
# ==========================================

@app.route(
    "/admin/clientes/<int:cliente_id>/eliminar",
    methods=["POST"]
)
@requiere_rol("administrador")
def admin_eliminar_cliente(cliente_id):

    conexion = obtener_conexion()

    try:
        with conexion.cursor() as cursor:

            cursor.execute("""
                SELECT id
                FROM usuarios
                WHERE id = %s
                AND rol = 'cliente'
                FOR UPDATE
            """, (cliente_id,))

            cliente = cursor.fetchone()

            if cliente is None:
                conexion.rollback()
                flash("El cliente no existe.")
                return redirect(url_for("admin_clientes"))

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM pedidos
                WHERE usuario_id = %s
            """, (cliente_id,))

            resultado = cursor.fetchone()

            if resultado["total"] > 0:
                conexion.rollback()
                flash(
                    "No es posible eliminar esta cuenta porque "
                    "tiene pedidos registrados. Se debe conservar "
                    "su historial de compras."
                )
                return redirect(
                    url_for(
                        "admin_detalle_cliente",
                        cliente_id=cliente_id
                    )
                )

            cursor.execute("""
                DELETE FROM usuarios
                WHERE id = %s
                AND rol = 'cliente'
            """, (cliente_id,))

            conexion.commit()
            flash("El cliente fue eliminado correctamente.")

    except pymysql.MySQLError:
        conexion.rollback()
        flash("Ocurrió un error al intentar eliminar al cliente.")

    finally:
        conexion.close()

    return redirect(url_for("admin_clientes"))


@app.route("/contacto")
def contacto():
    return render_template("contacto.html")


# ==========================================
# EJECUTAR APLICACIÓN
# ==========================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
