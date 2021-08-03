from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from haversine import haversine_vector, Unit
from deap import algorithms
from deap import base
from deap import creator
from deap import tools

import numpy
import array
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://bbbc511db8d449:e6f1c3ff@us-cdbr-east-04.cleardb.com/heroku_dcd450de6ec7181'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ma = Marshmallow(app)



class Punto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique = True)
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)

    def __init__(self, nombre, latitud, longitud):
        self.nombre = nombre
        self.latitud = latitud
        self.longitud = longitud
    
    def datos(self):
        return self.latitud, self.longitud
    
db.create_all()

class PuntoSchema(ma.Schema):
    class Meta:
        fields = ('id', 'nombre', 'latitud', 'longitud')

punto_schema = PuntoSchema()
puntos_schema = PuntoSchema(many=True)


# ---------- FUNCION PARA CREAR TABLA DISTANCIAS CON LAT Y LON
def calcular_distancias(puntos):
    l = len(puntos)
    arr_puntos = [(0, 0) for _ in range(l)]

    for i in range(l):
        arr_puntos[i] = puntos[i].datos()

    return haversine_vector(arr_puntos, arr_puntos, Unit.METERS, comb=True)



# ------------- REGISTRAR NUEVO PUNTO ---------------- #
@app.route('/punto', methods=['POST'])
def crearPunto():
    nombre = request.json['nombre']
    latitud = request.json['latitud']
    longitud = request.json['longitud']

    punto = Punto(nombre, latitud, longitud)

    db.session.add(punto)
    db.session.commit()
    
    return punto_schema.jsonify(punto)



# ------------- OBTENER TODOS LOS PUNTOS ---------------- #
@app.route('/puntos', methods=['GET'])
def getPuntos():
    puntos = Punto.query.all()
    resultado = puntos_schema.dump(puntos)
    print(puntos[0].nombre)
    return jsonify(resultado)


# ------------ OBTENER RUTA OPTIMA ------------------ #
@app.route('/ruta', methods=['GET'])
def getRuta():
    puntos = Punto.query.all()
    distance_map = calcular_distancias(puntos)
    IND_SIZE = len(puntos)

    print(distance_map)
    return jsonify(distance_map.tolist())



# ------------------- MAIN -------------------- #
if __name__ == "__main__":
    app.run(debug=True)