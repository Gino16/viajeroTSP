from flask import Flask, json, jsonify, request
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
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://doadmin:g2ww71b2e2xc8uq5@db-mysql-nyc3-78162-do-user-9244204-0.b.db.ondigitalocean.com:25060/viajerotsp'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/viajerotsp'

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
        rutaPuntos.append(puntos[ruta[i]])

    return jsonify({
        "ruta": puntos_schema.dump(rutaPuntos),
        "distancia": distancia[0]
    })


@app.route('/eliminar/<id>', methods=['DELETE'])
def deletePunto(id):
    punto = Punto.query.get(id)
    db.session.delete(punto)
    db.session.commit()
    return punto_schema.jsonify(punto)

@app.route('/eliminar/todo', methods=['DELETE'])
def deleteAll():
    db.session.query(Punto).delete()
    db.session.commit()
    return jsonify({"message": "Todos los registros eliminados"})

@app.route('/poblar-puntos', methods=['GET'])
def poblarPuntos():
    result = db.engine.execute("insert into punto (nombre, latitud, longitud) values ('Vivero de Nuevo Chimbote', -9.1291256, -78.5121042),('Felix', -9.136431071364676, -78.51728512227766),('Chaufa Talico', -9.1294528147166, -78.51683476078561),('Gino Ascencio', -9.12104925874468, -78.51622301047843),('Angel', -9.123907515727065, -78.53695434223293),('Jordan', -9.120472086100033, -78.54145720714085),('Patrick', -9.120875805901418, -78.53130984640943),('Juan', -9.126542914577833, -78.52909564202912),('Lupe Flores', -9.12744634385097, -78.51132850008365),('Rosa', -9.133221718400645, -78.50820097548838),('Restauran Gonzalito', -9.140053393612543, -78.50245802599576),('Pedro', -9.145431915493127, -78.50641923958972),('Foto Felix', -9.115997867739274, -78.54011943497542),('Marisol', -9.113962210824935, -78.5379981822419),('Panaderia Don Pedrito', -9.119905179218225, -78.5279401654431 ),('Gonzalo', -9.12302695324693, -78.51937298319774),('Sebastian', -9.120869018093508, -78.52185774200451),('Cevicheria Pescadito', -9.124005594635882, -78.5293550111817),('Teodoro', -9.12342842693463, -78.53014084257758),('Yessenia Cubas', -9.123731267830845, -78.52818824599588),('Ximena', -9.127151046290708, -78.53122342184238),('Mario', -9.126323158489592, -78.53212992222092),('Paula', -9.123133069733688, -78.53270785871882),('Milena', -9.139887987296426, -78.50152852625817),('Carlos', -9.137870102325, -78.50822666107541),('Julio', -9.136839856383366, -78.51263971724777),('Jaime Miranda', -9.134906142426487, -78.51794646983411),('Cesar Adolfo', -9.137053599520211, -78.52139791741868),('Pool Velasquez', -9.134545135954616, -78.52228724847704),('Andy Rosales', -9.134446563860122, -78.52369231269725),('Guillermo', -9.133348378106705, -78.52468613346109);")

    return jsonify({"message": "Nuevos puntos agregados"})

# ------------------- MAIN -------------------- #
if __name__ == "__main__":
    app.run(debug=True)
