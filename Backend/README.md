# Backend

## Dependencias
Este proyecto depende de:
- python 3.13
- docker engine

## Documentación

[En este enlace](https://docs.google.com/document/d/1tPlG_k7YH3RzEnt4lNGi-Q_tUiXHJjElLZet57OtsvM/edit?tab=t.0)

## Crear entorno virtual
Para separar las librerias a instalar en este proyecto, se recomienda crear un entorno virtual de python

``python -m venv .venv``

## Instalar proyecto
Para instalar el proyecto se debe ejecutar usando el entorno virtual de python (Activar con  ``. .venv/bin/activate``)

``make install-dev`` -> Esto va a instalar las librerias y crear un archivo .env (Hay que modificarlo con las credenciales de la base de datos y otras variables de entorno)

## Iniciar el proyecto
Primero levantar la base de datos con:

``make run-db``

Luego en otra terminal:

``make run``

