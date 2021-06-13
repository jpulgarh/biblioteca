#!/bin/bash

url=$1

function limitexmes() {
	if [ $mes -eq 01 ]; then return 31
	elif [ $mes -eq 02 ]; then return 28
	elif [ $mes -eq 03 ]; then return 31
	elif [ $mes -eq 04 ]; then return 30
	elif [ $mes -eq 05 ]; then return 30
	elif [ $mes -eq 06 ]; then return 31
	elif [ $mes -eq 07 ]; then return 31
	elif [ $mes -eq 08 ]; then return 30
	elif [ $mes -eq 09 ]; then return 31
	elif [ $mes -eq 10 ]; then return 31
	elif [ $mes -eq 11 ]; then return 30
	else return 31
	fi
}

if [ -z "$1" ] && [ -z "$2" ]; then
	echo "* Debes ejecutar ./convertir http://www.laserenaonline.cl/ 2020/02/ (para descargar todo febrero de 2020)"
	exit
else
	mes=$(echo $2 | awk -F / '{print $2}')
	echo ">>> Creando la carpeta $mes/"
	if [[ -d "$mes" ]]
	then
	  echo "Carpeta $mes ya existe en el sistema."
	else
		mkdir	$mes
	fi

	for (( x=1; x<31; x++))
	do
		#echo "* Eliminando el archivo index.html antiguo"
		rm -rf index.html

		if [ $x -eq 1 ]; then
			dia=01
		elif [ $x -eq 2 ]; then
			dia=02
		elif [ $x -eq 3 ]; then
			dia=03
		elif [ $x -eq 4 ]; then
			dia=04
		elif [ $x -eq 5 ]; then
			dia=05
		elif [ $x -eq 6 ]; then
			dia=06
		elif [ $x -eq 7 ]; then
			dia=07
		elif [ $x -eq 8 ]; then
			dia=08
		elif [ $x -eq 9 ]; then
			dia=09
		else
			dia=$x
		fi
		diarios=$url$2$dia'/feed/'
		#echo "* Descargando el sitemap $diarios"
		wget $diarios > /dev/null 2>&1

		#echo "* Dejando solo el link y guardando en noticias.txt"
		cat index.html | grep "<link>" | tr " \t" "\n" | tr -s "\n" | sed -e 's/^<link>//' -e 's/<\/link>$//' | sed '1,2d' > noticias.txt

		#echo "* Ahora vamos a descargar todos los link en pdf"
		while read line
		do
			#echo -e ">>> descargando $line"
			ar1=$(echo "$line" | sed 's/^.\{40\}//' | sed -e 's/.$//' | sed -e 's/-/_/g' | awk -F _ '{print $1 "_" $2 "_" $3 "_" $4 "_" $5}')
			ar2=$(echo "$ar1"".pdf")
			xvfb-run wkhtmltopdf $line $ar2 > /dev/null 2>&1
			sleep 1
		done < noticias.txt
	echo ">>> Creando el directorio $dia"
	mkdir $mes'/'$dia
	echo ">>> Moviendo los archivos pdf a $2"
	mv *.pdf $mes'/'$dia
	done

	echo "* Finalizando el proceso"
fi
