from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from haversine import haversine_vector, Unit
from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from flask_cors import CORS, cross_origin


import numpy
import array
import random

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://doadmin:g2ww71b2e2xc8uq5@db-mysql-nyc3-78162-do-user-9244204-0.b.db.ondigitalocean.com:25060/viajerotsp'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/viajerotsp'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ma = Marshmallow(app)


class Punto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True)
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
    if len(puntos) > 0:
        resultado = puntos_schema.dump(puntos)
        print(puntos[0].nombre)
        return jsonify(resultado)
    return jsonify({"message": "No existe puntos registrados"})


# ------------ ALGORITMO VIAJERO --------------------#
def viajero(distance_map, IND_SIZE):
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", array.array, typecode='I',
                   fitness=creator.FitnessMin)

    toolbox = base.Toolbox()

    toolbox.register("indices", random.sample, range(IND_SIZE), IND_SIZE)

    toolbox.register("individual", tools.initIterate,
                     creator.Individual, toolbox.indices)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evalTSP(individual):
        distance = distance_map[individual[-1]][individual[0]]
        for gene1, gene2 in zip(individual[0:-1], individual[1:]):
            distance += distance_map[gene1][gene2]
        return distance,

    toolbox.register("mate", tools.cxPartialyMatched)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=30)
    toolbox.register("evaluate", evalTSP)

    def main():
        random.seed(169)

        pop = toolbox.population(n=1000)

        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("min", numpy.min)

        algorithms.eaSimple(pop, toolbox, 0.7, 0.2, 40, stats=stats,
                            halloffame=hof)

        return hof

    hof = main()

    return hof, evalTSP(hof[0])


# ------------ OBTENER RUTA OPTIMA ------------------ #
@app.route('/ruta', methods=['GET'])
def getRuta():
    puntos = Punto.query.all()
    distance_map = calcular_distancias(puntos)
    IND_SIZE = len(puntos)

    puntos = Punto.query.all()  # Obteniendo todos los puntos de la bd

    rutaPuntos = []  # donde almacenaré la ruta a recorrer

    ruta, distancia = viajero(distance_map, IND_SIZE)
    ruta = str(ruta).split('[')[2].split(']')[0].split(',')  # capturando los indices
    ruta = list(map(int, ruta))  # convirtiendo indices a enteros

    for i in range(len(ruta)):
        rutaPuntos.append(puntos[i])

    print(distance_map)
    return jsonify({
        "ruta": puntos_schema.dump(rutaPuntos),
        "distancia": distancia[0]
    })


@app.route('/eliminar/<id>', methods=['DELETE'])
def deletePuntp(id):
    punto = Punto.query.get(id)
    db.session.delete(punto)
    db.session.commit()
    return punto_schema.jsonify(punto)

# ------------------- MAIN -------------------- #
if __name__ == "__main__":
    app.run(debug=True)
