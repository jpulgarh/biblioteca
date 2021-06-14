Script en BASH Linux que utiliza distintas herramientas para descargar noticias en lote desde WordPress y convertirlas a PDF con nombres limitados y en determinadas carpetas. El script funciona solo para páginas web de diarios digitales en WordPress y que tengan un formato de url http://dominio/año/mes/*

<h3>Modo de uso</h3>

1) Se debe descargar e instalar wkhtmltopdf desde https://wkhtmltopdf.org/downloads.html
2) Se debe ejecutar el script de la siguiente manera (Ejemplo): ./convertir http://www.laserenaonline.cl/ 2020/02/ (para descargar todo febrero de 2020)

Una vez descargadas las noticias en PDF y creadas sus respectivas carpetas, estas quedan listas para subirlas a la Biblioteca Nacional en su repositorio FTP.
