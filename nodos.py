from neo4j import GraphDatabase
import pandas as pd
import re, os
from dotenv import load_dotenv

load_dotenv()  # busca automáticamente un archivo llamado .env
#Se ejecuta en el import
uri = os.getenv('NEO4J_URI')
SUSER = os.getenv('NEO4J_USER')
password = os.getenv('NEO4J_PASSWORD')

neo4j = None
def conection(clave, usuario):
    global neo4j
    # Comprueba si la conexión ya ha sido establecida
    if neo4j is None:
        # Si no lo está, crea una nueva instancia de la conexión
        neo4j = Neo4jService(uri, SUSER, password)
    # Siempre ejecuta el __call__ (ya sea en la nueva instancia o en la ya existente)
    if(re.match(r'^OccX\d{4}$', clave) or re.match(r'^AL\d{3,4}$', clave) or re.match(r'^M\d{3}$', clave) or re.match(r'^LFM\d{3}$', clave)  ):
        neo4j(clave, usuario)
        return neo4j
    else:
        return neo4j

class Neo4jService:
    def __init__(self, uri, SUSER, password):
        self._driver = GraphDatabase.driver(uri, auth=(SUSER, password))
        self.asignatura = None
        self.unique_na  = None
        self.contador   = None
        self.Clave      = None
        self.user_      = None
        self.deleten = "no"
        self.deletey = "yes"
        self.pattern = r'^OccX\d{4}$'
        self.pattern0 = r'^AL\d{3,4}$'
        self.pattern1 = r'^M\d{3}$'
        self.pattern2 = r'^LFM\d{3}$'

    def __call__(self, clave, user_ ):

        self.user_   = user_

        if re.match(self.pattern, clave):
            self.Clave   = clave
            df_claves = pd.read_csv("CSV/OTRO/OTRO.csv")
        elif( re.match(self.pattern0, clave) or re.match(self.pattern1, clave) or re.match(self.pattern2, clave)   ):
            self.Clave   = clave
            df_claves = pd.read_csv("CSV/LIM_LFM_LMA.csv")
        else:
            self.Clave="OccX9999"

        self.asignatura = df_claves.loc[df_claves["Clave"]==self.Clave, ['Asignatura']].values.tolist()[0][0]
        self.unique_na = self.Clave + "0" + self.asignatura
        del df_claves

        nodo_q =   f""" MATCH (a:{self.Clave} {{name: $root}})
                        RETURN a.count
                    """
        nodo_params = {"root": self.unique_na}

        with self._driver.session() as session:
            result = session.run(nodo_q, nodo_params)
            single_result = result.single()

        self.contador = single_result[0] if single_result is not None else 0

        # Parámetros y Consulta
        a_query = f"MERGE (a:{self.Clave} {{index: 0, name: $unique_na, count: $count, delete: $delete}});"
        a_params = {"unique_na": self.unique_na, "count" : self.contador, "delete" : self.deleten}

        with self._driver.session() as session:
            session.run(a_query, a_params)
            
    def create_subtema(self, tema, subtema):
        nodo_q = f"""
        MATCH (a:{self.Clave} {{name: $root}})
        SET a.count = a.count + 1
        RETURN a.count
        """
        nodo_params = {"root": self.unique_na}

        with self._driver.session() as session:
            result        = session.run(nodo_q, nodo_params)
            subtema_index = result.single()[0]

        subtema = self.Clave + str(subtema_index) + subtema

        b_query = f"MERGE (b:{self.Clave}{{index: $subtema_index, name: $subtema, user:$user, delete:$delete}});"
        c_query = f"""
        MATCH (a:{self.Clave} {{name: $tema}}),
              (b:{self.Clave} {{name: $subtema}})
        MERGE (a)-[r:content]->(b)
        """
        d = self.deletey if self.user_ == "invitado" else self.deleten

        b_params = {"subtema_index": subtema_index, "subtema": subtema,"user":self.user_,"delete":d }
        c_params = {"tema": tema, "subtema": subtema}

        with self._driver.session() as session:
            session.run(b_query, b_params)
            session.run(c_query, c_params)

    def calificacion(self, tema, usuario, cal):
        c_query = f"""
        MATCH (a:{self.Clave} {{name: $tema}})
        MERGE (a)-[r:calificacion_user {{usuario: $usuario}}]->(a)
        ON CREATE SET r.metrica = $cal
        ON MATCH SET r.metrica = $cal
        """
        c_params = {"tema": tema, "usuario":usuario, "cal": cal}
        with self._driver.session() as session:
            session.run(c_query, c_params)

    def close(self):
        self._driver.close()

    def dellAll(self):
        with self._driver.session() as session:
            session.run("MATCH (n) detach delete n;")

    def delete(self,clave,padre,tema):
        dell = "no" if self.user_=="usuario1" else "yes" if self.user_=="invitado" else "no"

        query = f"""
                MATCH (tema:{clave} {{name: $tema}})
                MATCH (padre:{clave} {{name: $padre}})-[:content]->(tema)
                WHERE NOT ((tema)-[:content]->()) 
                DETACH DELETE tema
        """ #AND tema.delete = $no agrega antes del detach
        q_params = {"padre": padre, "tema": tema, "no":dell}
        with self._driver.session() as session:
            session.run(query, q_params)

    def get_subtemas(self,user):
        r_query = f"""


MATCH (n:{self.Clave})-[r:content]->(m:{self.Clave})
WITH n, r, m, coalesce([(m)-[c:calificacion_user {{usuario: $user}}]->(m) | c.metrica][0], 0) AS calificaciones2
WITH n, r, m, calificaciones2, m.user as usser, [(m)-[c2:calificacion_user]->(m) | c2.metrica] AS allMetrics
RETURN n, r, m, calificaciones2, usser, coalesce(abs(round(reduce(s=0, x IN allMetrics | s + x)/(size(allMetrics)+0.000001))), 0) as avgMetrica
ORDER BY m.index;

        """
        r_params = {"user":user}
        with self._driver.session() as session:
            result = session.run(r_query,r_params)
            nodes = [record for record in result]
        return nodes

    def get_subtemas1(self):
        r_query = f"""
            MATCH (n:{self.Clave} )
            RETURN n;
            """
        with self._driver.session() as session:
            result = session.run(r_query)
            nodes = [record for record in result]
        return nodes

    def cal_root(self,user):
        r_query=f"""
        MATCH (n:{self.Clave} {{ name: $tema}})
        WITH n, coalesce([(n)-[c:calificacion_user {{usuario: $user}} ]->(n) | c.metrica][0],0) AS cal_root
        RETURN cal_root
        """
        r_params = {"tema":self.unique_na,"user":user}
        with self._driver.session() as session:
            result = session.run(r_query,r_params)
            nodes = [record for record in result]
        return nodes[0].value()

def build_tree(node, tree, visited):
    if node not in tree or node in visited:
        return {}
    visited.add(node)
    return {child[0]: {"calificacion": child[1], **build_tree(child[0], tree, visited)} for child in tree[node]}

arbol = None
def tree(clave,usuario):
    global arbol                         
    neo4j = conection(clave, usuario)
    n     = neo4j.get_subtemas(usuario)
    data  = []
    for i in range(len(n)):
        a = n[i]["n"].get("name")
        b = n[i]["m"].get("name")
        d = n[i]["calificaciones2"]
        z = n[i]["usser"]
        y = str(int(n[i]["avgMetrica"]))
        data.append([a,[b,str(d)+y+z]])

    tree = {}
    root_calificacion = neo4j.cal_root(usuario)  # Calificación que desees para el nodo raíz
    for pair in data:
        if pair[0] not in tree:
            tree[pair[0]] = []
        tree[pair[0]].append(pair[1])  
    if not bool( list( tree.keys() ) ):
        n = neo4j.get_subtemas1()
        c = []
        for i in range(len(n)):
            a = n[i]["n"].get("name")
            c.append([a])
        arbol = {c[0][0]:{}}
    else:
        root  = list(tree.keys())[0]
        arbol = {root: {"calificacion": root_calificacion, **build_tree(root, tree, set())}}  # Agrega calificación al nodo raíz aquí
    return arbol

def agregar(clave, tema, subtema,usuario):
    neo4j = conection(clave, usuario)
    neo4j.create_subtema(tema=tema, subtema=subtema)

def delete(clave, padre, tema, usuario):
    neo4j = conection(clave, usuario)
    neo4j.delete(clave=clave,padre=padre,tema=tema,)

def calificacion(clave, tema, calificacion, usuario):
    neo4j = conection(clave, usuario)
    neo4j.calificacion(tema=tema, usuario=usuario, cal=calificacion)

if __name__ == "__main__":
    print("Prueba de concepto para ejectar codigo desde este mismo")
    #No se ejecuta en el import