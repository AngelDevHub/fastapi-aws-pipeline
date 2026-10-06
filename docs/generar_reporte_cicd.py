"""Genera el reporte de la práctica de CI/CD en PDF.

Uso:  python generar_reporte_cicd.py
Para meter tus capturas, pon los archivos en la carpeta capturas/ con los
nombres de abajo (CAPTURAS). Si el archivo no existe, se deja un recuadro vacío.
"""
import os
from datetime import datetime
from fpdf import FPDF, XPos, YPos

# ---- Rutas y configuración --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOR = "Jose Angel Gomez Castañon"
MATRICULA = "2023371222"
PROFESOR = "Emmanuel Martinez Hernandez"
MATERIA = "Gestión del Proceso de Desarrollo de Software"
SALIDA = os.path.join(BASE_DIR, "Reporte_CICD.pdf")
CARPETA_IMG = os.path.join(BASE_DIR, "capturas")

# Paleta
AZUL = (31, 64, 104)
ACENTO = (224, 122, 47)
GRIS = (95, 99, 104)
GRIS_CLARO = (243, 244, 246)
TEXTO = (33, 37, 41)

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga():
    h = datetime.now()
    return f"{h.day} de {MESES[h.month - 1]} de {h.year}"


class Reporte(FPDF):
    def __init__(self):
        super().__init__(format="Letter")
        self.set_margins(22, 22, 22)
        self.set_auto_page_break(True, margin=22)
        self.n_fig = 0
        self.portada = True

    def header(self):
        # sin encabezado en las páginas interiores
        self.set_y(22)

    def footer(self):
        if self.portada:
            return
        self.set_y(-16)
        self.set_draw_color(210, 214, 220)
        self.set_line_width(0.2)
        self.line(22, self.get_y(), self.w - 22, self.get_y())
        self.ln(2)
        self.set_font("helvetica", "", 8.5)
        self.set_text_color(*GRIS)
        self.cell(0, 5, f"{MATERIA}", align="L")
        self.set_x(22)
        self.cell(0, 5, f"{self.page_no() - 1}", align="R")

    # ---- elementos de texto ----
    def seccion(self, num, titulo):
        if self.get_y() > self.h - 70:
            self.add_page()
        self.ln(6)
        y = self.get_y()
        self.set_xy(22, y)
        self.set_font("helvetica", "B", 22)
        self.set_text_color(*ACENTO)
        self.cell(13, 10, f"{num:02d}")
        self.set_font("helvetica", "B", 15)
        self.set_text_color(*AZUL)
        self.cell(0, 10, titulo, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*AZUL)
        self.set_line_width(0.4)
        self.line(22, y + 11.5, self.w - 22, y + 11.5)
        self.set_y(y + 16)

    def subtitulo(self, texto):
        self.set_font("helvetica", "B", 11)
        self.set_text_color(*AZUL)
        self.cell(0, 7, texto, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def parrafo(self, texto):
        self.set_font("helvetica", "", 10.5)
        self.set_text_color(*TEXTO)
        self.multi_cell(0, 5.8, texto, align="J")
        self.ln(2.5)

    def lista(self, items):
        self.set_font("helvetica", "", 10.5)
        self.set_text_color(*TEXTO)
        for it in items:
            self.set_x(26)
            self.set_text_color(*ACENTO)
            self.cell(5, 5.8, "-")
            self.set_text_color(*TEXTO)
            self.multi_cell(0, 5.8, it)
        self.ln(2.5)

    def codigo(self, texto):
        lineas = texto.strip("\n").split("\n")
        alto = 5 * len(lineas) + 6
        if self.get_y() + alto > self.h - 25:
            self.add_page()
        y = self.get_y()
        self.set_fill_color(*GRIS_CLARO)
        self.rect(22, y, self.w - 44, alto, "F")
        self.set_fill_color(*AZUL)
        self.rect(22, y, 1.2, alto, "F")
        self.set_font("courier", "", 9)
        self.set_text_color(*TEXTO)
        self.set_xy(27, y + 3)
        for ln in lineas:
            self.set_x(27)
            self.cell(0, 5, ln, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(y + alto + 4)

    def tabla(self, cabecera, filas, anchos):
        self.set_font("helvetica", "B", 9.5)
        self.set_fill_color(*AZUL)
        self.set_text_color(255, 255, 255)
        for t, a in zip(cabecera, anchos):
            self.cell(a, 8, f" {t}", fill=True)
        self.ln()
        self.set_font("helvetica", "", 9.5)
        self.set_text_color(*TEXTO)
        for i, fila in enumerate(filas):
            self.set_fill_color(*(GRIS_CLARO if i % 2 == 0 else (255, 255, 255)))
            for t, a in zip(fila, anchos):
                self.cell(a, 8, f" {t}", fill=True)
            self.ln()
        self.ln(4)

    def figura(self, descripcion, archivo, max_alto=90):
        """Pone la imagen si existe en la raíz o en capturas/; si no, un recuadro."""
        self.n_fig += 1
        
        # Buscar en la misma carpeta o en capturas/
        ruta = archivo
        if not os.path.exists(ruta):
            ruta = os.path.join(CARPETA_IMG, archivo)

        ancho_util = self.w - 44
        x = 22

        if os.path.exists(ruta):
            try:
                from PIL import Image
                with Image.open(ruta) as im:
                    w_orig, h_orig = im.size
                alto_calculado = ancho_util * (h_orig / w_orig)
                
                # Si es demasiado alta, la limitamos para que no desborde la página
                if alto_calculado > max_alto:
                    alto_calculado = max_alto
                    w_img = alto_calculado * (w_orig / h_orig)
                    x_img = x + (ancho_util - w_img) / 2
                else:
                    w_img = ancho_util
                    x_img = x

                # Si no cabe en la página actual, saltar de página
                if self.get_y() + alto_calculado + 14 > self.h - 22:
                    self.add_page()

                y = self.get_y()
                self.image(ruta, x=x_img, y=y, w=w_img, h=alto_calculado)
                self.set_y(y + alto_calculado + 2)
            except Exception as e:
                print(f"Error cargando imagen {ruta}: {e}")
                self.ln(2)
        else:
            alto = 50
            if self.get_y() + alto + 14 > self.h - 22:
                self.add_page()
            y = self.get_y()
            self.set_draw_color(190, 194, 200)
            self.set_fill_color(250, 250, 251)
            self.set_line_width(0.3)
            self.set_dash_pattern(dash=2, gap=2)
            self.rect(x, y, ancho_util, alto, "DF")
            self.set_dash_pattern()
            self.set_xy(x, y + alto / 2 - 4)
            self.set_font("helvetica", "I", 9.5)
            self.set_text_color(160, 164, 170)
            self.cell(ancho_util, 8, f"Captura no encontrada: {archivo}", align="C")
            self.set_y(y + alto + 2)

        self.set_font("helvetica", "I", 9)
        self.set_text_color(*GRIS)
        self.cell(0, 6, f"Figura {self.n_fig}. {descripcion}", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)


pdf = Reporte()

# ---- Portada ---------------------------------------------------------------
pdf.add_page()
pdf.set_fill_color(*AZUL)
pdf.rect(0, 0, 14, pdf.h, "F")
pdf.set_fill_color(*ACENTO)
pdf.rect(14, 0, 2.5, pdf.h, "F")

pdf.set_xy(32, 70)
pdf.set_font("helvetica", "", 11)
pdf.set_text_color(*GRIS)
pdf.cell(0, 6, MATERIA.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

pdf.set_x(32)
pdf.set_font("helvetica", "B", 30)
pdf.set_text_color(*AZUL)
pdf.multi_cell(150, 13, "Implementación de un pipeline CI/CD")
pdf.set_x(32)
pdf.set_font("helvetica", "", 15)
pdf.set_text_color(*TEXTO)
pdf.ln(2)
pdf.multi_cell(150, 8, "API en FastAPI, Docker, GitHub Actions y despliegue en AWS EC2")

pdf.set_fill_color(*ACENTO)
pdf.rect(32, pdf.get_y() + 8, 30, 1.2, "F")

pdf.set_xy(32, 190)
pdf.set_font("helvetica", "B", 10.5)
pdf.set_text_color(*TEXTO)
pdf.cell(0, 5.5, f"Alumno: {AUTOR}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_x(32)
pdf.set_font("helvetica", "", 10)
pdf.set_text_color(*GRIS)
pdf.cell(0, 5.5, f"Matrícula: {MATRICULA}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_x(32)
pdf.cell(0, 5.5, f"Profesor: {PROFESOR}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_x(32)
pdf.cell(0, 5.5, f"Fecha: {fecha_larga()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

pdf.portada = False
pdf.add_page()

# ---- 1. Introducción -------------------------------------------------------
pdf.seccion(1, "Introducción")
pdf.parrafo(
    "En esta práctica armé un flujo de integración y despliegue continuo para una API "
    "hecha con FastAPI. La idea es que cada vez que subo un cambio a la rama main, el "
    "código se pruebe solo, se empaquete en una imagen de Docker y se publique en un "
    "servidor de AWS sin que yo tenga que entrar a la máquina a hacer nada a mano."
)
pdf.parrafo(
    "Antes de llegar al despliegue tuve que cumplir con un mínimo de 70% de cobertura "
    "de pruebas, así que gran parte del trabajo fue ajustar los tests y la configuración "
    "de coverage. Al final también tuve varios errores con SSH y con la red de AWS, que "
    "explico en la sección de problemas."
)

pdf.subtitulo("Herramientas utilizadas")
pdf.tabla(
    ["Herramienta", "Para qué se usó"],
    [
        ["FastAPI", "API REST con el endpoint /api/health"],
        ["Pytest + coverage", "Pruebas y medición de cobertura"],
        ["Docker / Docker Hub", "Imagen de la aplicación y registro"],
        ["GitHub Actions", "Automatización del pipeline"],
        ["AWS EC2 (Ubuntu)", "Servidor donde corre el contenedor"],
    ],
    [55, 115],
)

# ---- 2. Pruebas ------------------------------------------------------------
pdf.seccion(2, "Pruebas y cobertura")
pdf.parrafo(
    "Las pruebas se escribieron con Pytest. El pipeline falla si la cobertura baja de "
    "70%, por lo que lo primero fue revisar qué archivos estaban bajando el porcentaje. "
    "Los módulos del servidor TCP y la generación de PDFs no forman parte de la API, así "
    "que los excluí en el archivo .coveragerc y marqué con pragma: no cover las partes "
    "que no se pueden probar de forma sencilla."
)
pdf.parrafo(
    "En GitHub Actions tuve que ejecutar las pruebas con python -m pytest en lugar de "
    "solo pytest, porque de la otra forma no encontraba los módulos del proyecto."
)
pdf.codigo("python -m pytest --cov=. --cov-fail-under=70")
pdf.figura("Resultado de pytest con el porcentaje de cobertura.", "cobertura.png")

# ---- 3. Docker -------------------------------------------------------------
pdf.seccion(3, "Contenedor con Docker")
pdf.parrafo(
    "El Dockerfile parte de una imagen ligera de Python y usa dos etapas: en la primera "
    "se instalan las dependencias y en la segunda solo se copia lo necesario para correr "
    "la app. Además, el contenedor no corre como root sino con un usuario normal, y agregué "
    "un .dockerignore para no meter archivos que no hacen falta (venv, caché, etc.)."
)
pdf.figura("Imagen publicada en Docker Hub.", "dockerhub.png")

# ---- 4. Pipeline -----------------------------------------------------------
pdf.seccion(4, "Pipeline en GitHub Actions")
pdf.parrafo(
    "El workflow se dispara con cada push a main y tiene tres jobs que se ejecutan en "
    "orden. Si uno falla, los siguientes no corren."
)
pdf.tabla(
    ["Job", "Qué hace"],
    [
        ["test", "Instala dependencias y corre pytest con cobertura"],
        ["build-and-push", "Construye la imagen y la sube a Docker Hub"],
        ["deploy-ec2", "Se conecta por SSH a EC2 y actualiza el contenedor"],
    ],
    [55, 115],
)
pdf.parrafo(
    "Las credenciales (usuario y token de Docker Hub, IP del servidor, usuario y llave "
    "SSH) están guardadas como secretos del repositorio, no en el código."
)
pdf.figura("Los tres jobs del pipeline completados en verde.", "pipeline.png")

# ---- 5. AWS ----------------------------------------------------------------
pdf.seccion(5, "Despliegue en AWS EC2")
pdf.parrafo(
    "El último job entra al servidor Ubuntu por SSH, descarga la imagen más reciente, "
    "detiene el contenedor anterior y levanta el nuevo en el puerto 80. Para poder ver la "
    "API desde el navegador hubo que abrir el puerto 80 en el Security Group de la instancia."
)
pdf.codigo(
    "GET http://<IP-publica>/api/health\n"
    '{"status": "ok", "environment": "production"}'
)
pdf.figura("Respuesta de la API en el navegador usando la IP pública de EC2.", "api_aws.png")

# ---- 6. Problemas ----------------------------------------------------------
pdf.seccion(6, "Problemas que tuve")
pdf.lista([
    "Error de autenticación SSH: el usuario correcto en Ubuntu era 'ubuntu' y en el secreto "
    "había que pegar la llave .pem completa, con sus líneas BEGIN y END.",
    "Timeout al abrir la IP: faltaba permitir tráfico HTTP (puerto 80) en el Security Group.",
    "Pytest no encontraba los módulos en el pipeline: se arregló usando python -m pytest.",
    "La cobertura no llegaba al mínimo: se excluyeron los módulos ajenos a la API.",
])

# ---- 7. Conclusión ---------------------------------------------------------
pdf.seccion(7, "Conclusiones")
pdf.parrafo(
    "Lo que más me sirvió de la práctica fue ver el flujo completo funcionando: un cambio "
    "en el código termina en producción en pocos minutos y con las pruebas ya validadas. "
    "También me quedó claro que la mayoría de los errores estuvieron en la configuración "
    "(secretos, red, permisos) y no en el código de la aplicación."
)

pdf.output(SALIDA)
print(f"Listo: {SALIDA}")
