# coding: utf-8
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Optional

errores_sem = []

CLASES_BASICAS = {"Object", "Int", "Bool", "String", "IO", "SELF_TYPE"}
HERENCIAS_BASICAS = {clase:"Object" for clase in list(CLASES_BASICAS)}
METODOS_BASICOS = {"abort", "type_name", "copy", "length"}


def add_error(msg):
    if msg not in errores_sem:
        errores_sem.append(msg)

class Ambito:
    clases: dict[str, 'Ambito'] = {}
    ambitos: List['Ambito'] = []
    arbol_herencias: dict[str, 'Clase'] = {}
    herencias_por_nombre: dict[str, str] = HERENCIAS_BASICAS.copy()
    clases_por_nombre: dict[str, 'Clase'] = {}

    def __init__(self, padre: Optional['Ambito'] = None):
        self.padre = padre
        self.variables: dict[str, str] = {}
        self.metodos: dict[str, Metodo] = {}

        for clase in CLASES_BASICAS:
            if clase == "Object":
                self.set_ambito_clase(clase, self)
                self.anhadir_clase(Clase(nombre="Object", padre="Object",
                                     caracteristicas=[Caracteristica(0, "Object", "Object")]),
                                     #Faltan los métodos (?)
                                     "Object")
            elif clase == "Int":
                self.set_ambito_clase(clase, self)
                self.anhadir_clase(Clase(nombre="Int", padre="Object",
                                     caracteristicas=[Caracteristica(0, "Int", "Int")]),
                                     #Faltan los métodos (?)
                                     "Object")
            elif clase == "Bool":
                self.set_ambito_clase(clase, self)
                self.anhadir_clase(Clase(nombre="Bool", padre="Object",
                                     caracteristicas=[Caracteristica(0, "Bool", "Bool")]),
                                     #Faltan los métodos (?)
                                     "Object")
            elif clase == "String":
                self.set_ambito_clase(clase, self)
                self.anhadir_clase(Clase(nombre="String", padre="Object",
                                     caracteristicas=[Caracteristica(0, "String", "String")]),
                                     #Faltan los métodos (?)
                                     "Object")
            elif clase == "IO":
                self.set_ambito_clase(clase, self)
                self.anhadir_clase(Clase(nombre="IO", padre="Object",
                                     caracteristicas=[Caracteristica(0, "IO", "IO")]),
                                     #Faltan los métodos (?)
                                     "Object")
        
    #TODO: Posiblemente los métodos registrar_clase y anhadir_clase
    #    debieran refactorizarse en un sólo método.
    def registrar_clase(self, nombre: str, clase: 'Clase'):
        #print("DEBUG:", clase.nombre, clase.linea)
        if nombre in CLASES_BASICAS:
            errores_sem.append(
                f"{clase.linea + 1}: Redefinition of basic class {nombre}."
            )
            return

        if nombre in Ambito.clases_por_nombre:
            errores_sem.append(
                f"{clase.linea + 1}: Class {nombre} was previously defined."
            )
        else:
            Ambito.clases_por_nombre[nombre] = clase

    def anhadir_clase(self, clase, padre):
        self.arbol_herencias[clase.nombre] = padre #if isinstance(padre, str) else padre.nombre
        self.herencias_por_nombre[clase.nombre] = padre
        cars_padre: dict[str, 'Caracteristica'] = {}

        if padre != 'Object':
            for c in self.clases_por_nombre.get(padre, Clase()).caracteristicas:
                cars_padre[c.nombre] = c
            for caracteristica in clase.caracteristicas:
                if isinstance(caracteristica, Metodo):
                    self.add_metodo(caracteristica.nombre, caracteristica)
                    if caracteristica.nombre in cars_padre:
                        if len(caracteristica.formales) != len(cars_padre[caracteristica.nombre].formales):
                            errores_sem.append(f"{caracteristica.linea}: Incompatible number of formal parameters in redefined method {caracteristica.nombre}.")
                        car_padre = cars_padre[caracteristica.nombre]
                        for formal in caracteristica.formales:
                            for f in car_padre.formales:
                                if formal.nombre_variable == f.nombre_variable and formal.tipo != f.tipo:
                                    errores_sem.append(f"{caracteristica.linea}: In redefined method {caracteristica.nombre}, parameter type {formal.tipo} is different from original type {f.tipo}")

    def get_ambito_clase(self, nombre: str) -> Optional['Ambito']:
        if nombre in self.clases:
            return self.clases[nombre]
        else:
            return None
        
    def set_ambito_clase(self, nombre: str, ambito: 'Ambito'):
        Ambito.clases[nombre] = ambito

    def get_metodo(self, nombre: str) -> Optional['Metodo']:
        if nombre in self.metodos:
            return self.metodos[nombre]
        elif self.padre:
            return self.padre.get_metodo(nombre)
        else:
            return None
    
    def add_metodo(self, nombre: str, metodo: 'Metodo'):
        self.metodos[nombre] = metodo
    
    def get_tipo_variable(self, nombre: str) -> Optional[str]:
        if nombre in self.variables:
            return self.variables[nombre]
        elif self.padre:
            return self.padre.get_tipo_variable(nombre)
        else:
            return None
        
    def add_variable(self, nombre: str, tipo: str):
        self.variables[nombre] = tipo
    
    def es_subtipo(self, tipo1: str, tipo2: str) -> bool:
        if tipo1 == tipo2 or self.mca(tipo1, tipo2) == tipo2:
            return True
        elif tipo1 == 'Object':
            return False
        else:
            return False

    def mca(self, tipo1: str, tipo2: str) -> str:
        lista_1 = [tipo1]
        current_elem = tipo1
        while current_elem != "Object":
            current_elem = self.herencias_por_nombre[current_elem]
            lista_1.append(current_elem)

        current_elem = tipo2
        while current_elem not in lista_1:
            current_elem = self.herencias_por_nombre[current_elem]
        
        return current_elem

    def entrar_ambito(self):
        nuevo_ambito = deepcopy(Ambito(padre=self))
        self.ambitos.append(nuevo_ambito)
        return nuevo_ambito

    def salir_ambito(self):
        if self.ambitos:
            return self.ambitos.pop()
        else:
            return None
        

@dataclass
class Nodo:
    linea: int = 0

    def str(self, n):
        return f'{n*" "}#{self.linea}\n'


@dataclass
class Formal(Nodo):
    nombre_variable: str = '_no_set'
    tipo: str = '_no_type'
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_formal\n'
        resultado += f'{(n+2)*" "}{self.nombre_variable}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        return resultado
    def Tipo(self, ambito: Ambito):
        if self.nombre_variable == 'self':
            errores_sem.append(
                f"{self.linea}: 'self' cannot be the name of a formal parameter."
            )
        if self.nombre_variable in ambito.variables:
            errores_sem.append(
                f"{self.linea}: Formal parameter {self.nombre_variable} is multiply defined."
            )
        if self.tipo == 'SELF_TYPE':
            errores_sem.append(
                f"{self.linea}: Formal parameter {self.nombre_variable} cannot have type {self.tipo}."
            )
        
        ambito.add_variable(self.nombre_variable, self.tipo)




class Expresion(Nodo):
    cast: str = '_no_type'
    
    def Tipo(self, ambito: Ambito):
        pass


@dataclass
class Asignacion(Expresion):
    nombre: str = '_no_set'
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_assign\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, ambito: Ambito):
        self.cuerpo.Tipo(ambito)

        tipo_var = ambito.get_tipo_variable(self.nombre)
        tipo_expr = self.cuerpo.cast

        # si la variable no existe
        if tipo_var is None:
            errores_sem.append(f"{self.linea}: Undeclared identifier {self.nombre}.")
            self.cast = tipo_expr
            return

        if not ambito.es_subtipo(tipo_expr, tipo_var):
            errores_sem.append(
                f"{self.linea}: Type {tipo_expr} of assigned expression does not conform to declared type {tipo_var} of identifier {self.nombre}."
            )

        self.cast = tipo_expr


@dataclass
class LlamadaMetodoEstatico(Expresion):
    cuerpo: Expresion = None
    clase: str = '_no_type'
    nombre_metodo: str = '_no_set'
    argumentos: List[Expresion] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_static_dispatch\n'
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n+2)*" "}{self.clase}\n'
        resultado += f'{(n+2)*" "}{self.nombre_metodo}\n'
        resultado += f'{(n+2)*" "}(\n'
        resultado += ''.join([c.str(n+2) for c in self.argumentos])
        resultado += f'{(n+2)*" "})\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado

    def Tipo(self, ambito: Ambito):
        for arg in self.argumentos:
            arg.Tipo(ambito)
        self.cuerpo.Tipo(ambito)
        ambito_clase = ambito.get_ambito_clase(self.clase)
        if ambito.mca(self.cuerpo.cast, self.clase) != self.clase:
            errores_sem.append(
                f"{self.linea}: Expression type {self.cuerpo.cast} does not conform to declared static dispatch type {self.clase}."
            )
            self.cast = 'Object'
        else:
            if ambito_clase is None:
                metodo = ambito.get_metodo(self.nombre_metodo)
            else:
                metodo = ambito_clase.get_metodo(self.nombre_metodo)
            if metodo is None or metodo.tipo == 'SELF_TYPE':
                self.cast = self.cuerpo.cast
            else:
                self.cast = metodo.tipo


@dataclass
class LlamadaMetodo(Expresion):
    cuerpo: Expresion = None
    nombre_metodo: str = '_no_set'
    argumentos: List[Expresion] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_dispatch\n'
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n+2)*" "}{self.nombre_metodo}\n'
        resultado += f'{(n+2)*" "}(\n'
        resultado += ''.join([c.str(n+2) for c in self.argumentos])
        resultado += f'{(n+2)*" "})\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado

    def valor(self, ambito):
        cuerpo_ret = self.cuerpo.valor(ambito)
        if self.nombre_metodo == 'copy':
            return cuerpo_ret
        elif self.nombre_metodo == 'abort':
            exit()
            
    def Tipo(self, ambito: Ambito):

        if getattr(self, "_visited", False):
            return
        self._visited = True

        for arg in self.argumentos:
            if arg.cast == '_no_type':
                arg.Tipo(ambito)

        self.cuerpo.Tipo(ambito)

        metodo = None
        if self.cuerpo is None:
            clase_nombre = ambito.tipo_clase_actual
        elif self.cuerpo.cast == 'SELF_TYPE':
            clase_nombre = ambito.tipo_clase_actual
        else:
            clase_nombre = self.cuerpo.cast

        #print(f"Analizando llamada a mÃ©todo {self.nombre_metodo} en la clase {clase_nombre}")

        if clase_nombre is not None and metodo is None:
            clase = Ambito.clases_por_nombre.get(clase_nombre)
            if clase and clase.ambito:
                clase.Tipo(clase.ambito)
                metodo = clase.ambito.get_metodo(self.nombre_metodo)
                clase_nombre = Ambito.arbol_herencias.get(clase_nombre)
        
        if self.nombre_metodo not in clase.ambito.metodos and clase_nombre is not None:
            add_error(
                f"{self.linea}: Dispatch to undefined method {self.nombre_metodo}."
            )
            
        #TODO: Esto es un apaño. Habrá que generalizarlo y expandirlo a los demás métodos o extraerlo 
        #   al bucle que crea las clases básicas en Ambito.__init__()
        ####
        elif clase_nombre in CLASES_BASICAS:
            if self.nombre_metodo in METODOS_BASICOS:
                metodo = Metodo(nombre=self.nombre_metodo, tipo='int' if self.nombre_metodo == 'length' 
                                else 'SELF_TYPE', formales=[])
        #### Fin del apaño
        
        elif metodo is None:
            add_error(
                f"{self.linea}: Dispatch to undefined method {self.nombre_metodo}."
            )
            self.cast = 'Object'
            return

        if len(metodo.formales) == len(self.argumentos) and not hasattr(self, "_checked_args"):
            self._checked_args = True
            for formal, arg in zip(metodo.formales, self.argumentos):
                if not ambito.es_subtipo(arg.cast, formal.tipo):
                    add_error(
                        f"{self.linea}: In call of method {self.nombre_metodo}, "
                        f"type {arg.cast} of parameter {formal.nombre_variable} "
                        f"does not conform to declared type {formal.tipo}."
                    )

        if metodo.tipo == 'SELF_TYPE':
            self.cast = self.cuerpo.cast
        else:
            self.cast = metodo.tipo
        

@dataclass
class Condicional(Expresion):
    condicion: Expresion = None
    verdadero: Expresion = None
    falso: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_cond\n'
        resultado += self.condicion.str(n+2)
        resultado += self.verdadero.str(n+2)
        resultado += self.falso.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado        
        
    def Tipo(self, ambito: Ambito):
        self.condicion.Tipo(ambito)
        self.verdadero.Tipo(ambito)
        self.falso.Tipo(ambito)
        tipo_v = self.verdadero.cast
        tipo_f = self.falso.cast
        if self.condicion.cast == 'Bool':
            self.cast = ambito.mca(tipo_v, tipo_f)


@dataclass
class Bucle(Expresion):
    condicion: Expresion = None
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_loop\n'
        resultado += self.condicion.str(n+2)
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    def Tipo(self, ambito: Ambito):
        self.condicion.Tipo(ambito)
        self.cuerpo.Tipo(ambito)

        if self.condicion.cast != 'Bool':
            errores_sem.append(
                f"{self.linea}: Loop condition does not have type Bool."
            )

        self.cast = 'Object'


@dataclass
class Let(Expresion):
    nombre: str = '_no_set'
    tipo: str = '_no_set'
    inicializacion: Expresion = None
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_let\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += self.inicializacion.str(n+2)
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, ambito: Ambito):
        ambito_let = Ambito(padre=ambito)

        self.inicializacion.Tipo(ambito_let)

        if self.inicializacion.cast != '_no_type' and self.tipo != '_no_set':
            if not ambito.es_subtipo(self.inicializacion.cast, self.tipo):
                errores_sem.append(
                    f"{self.linea}: Inferred type {self.inicializacion.cast} of initialization of {self.nombre} does not conform to identifier's declared type {self.tipo}."
                )
        if self.nombre == 'self':
            errores_sem.append(
                f"{self.linea}: 'self' cannot be bound in a 'let' expression."
            )

        ambito_let.add_variable(self.nombre, self.tipo)

        self.cuerpo.Tipo(ambito_let)

        self.cast = self.cuerpo.cast
        


@dataclass
class Bloque(Expresion):
    expresiones: List[Expresion] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado = f'{n*" "}_block\n'
        resultado += ''.join([e.str(n+2) for e in self.expresiones])
        resultado += f'{(n)*" "}: {self.cast}\n'
        resultado += '\n'
        return resultado
    
    def Tipo(self, ambito: Ambito):
        for expr in self.expresiones:
            expr.Tipo(ambito)
        if self.expresiones:
            self.cast = self.expresiones[-1].cast
        else:
            self.cast = 'Object'


@dataclass
class RamaCase(Nodo):
    nombre_variable: str = '_no_set'
    tipo: str = '_no_set'
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_branch\n'
        resultado += f'{(n+2)*" "}{self.nombre_variable}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += self.cuerpo.str(n+2)
        return resultado
    
    def Tipo(self, ambito: Ambito):
        ambito_branch = Ambito(padre=ambito)
        ambito_branch.add_variable(self.nombre_variable, self.tipo)
        self.cuerpo.Tipo(ambito_branch)


@dataclass
class Swicht(Nodo):
    expr: Expresion = None
    casos: List[RamaCase] = field(default_factory=list)
    cast: str = '_no_type'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_typcase\n'
        resultado += self.expr.str(n+2)
        resultado += ''.join([c.str(n+2) for c in self.casos])
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    def Tipo(self, ambito: Ambito):
        self.expr.Tipo(ambito)
        tipos_vistos = set()
        for caso in self.casos:
            if caso.tipo in tipos_vistos:
                errores_sem.append(
                    f"{caso.linea}: Duplicate branch {caso.tipo} in case statement."
                )
            else:
                tipos_vistos.add(caso.tipo)

            caso.Tipo(ambito)
        tipos_casos = [caso.cuerpo.cast for caso in self.casos]
        if tipos_casos:
            self.cast = tipos_casos[0]
            for tipo in tipos_casos[1:]:
                if not ambito.es_subtipo(tipo, self.cast):
                    if ambito.es_subtipo(self.cast, tipo):
                        self.cast = tipo
                    else:
                        self.cast = 'Object'
                        break
        else:
            self.cast = 'Object'

@dataclass
class Nueva(Nodo):
    tipo: str = '_no_set'
    cast: str = '_no_type'
    
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_new\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, ambito):
        if self.tipo not in Ambito.clases_por_nombre and self.tipo not in CLASES_BASICAS:
            errores_sem.append(
                f"{self.linea}: 'new' used with undefined class {self.tipo}."
            )
        self.cast = self.tipo


@dataclass
class OperacionBinaria(Expresion):
    izquierda: Expresion = None
    derecha: Expresion = None
    
    def Tipo(self, ambito):
        self.izquierda.Tipo(ambito)
        self.derecha.Tipo(ambito)
        if self.izquierda.cast == self.derecha.cast:
            self.cast = self.izquierda.cast
        else:
            self.cast = 'Object'


@dataclass
class Suma(OperacionBinaria):
    operando: str = '+'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_plus\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado

    def Tipo(self, ambito):
        self.izquierda.Tipo(ambito)
        self.derecha.Tipo(ambito)

        tipo_izq = self.izquierda.cast
        tipo_der = self.derecha.cast

        if tipo_izq != 'Int' or tipo_der != 'Int':
            errores_sem.append(
                f"{self.linea}: non-Int arguments: {tipo_izq} + {tipo_der}"
            )

        self.cast = 'Int'  # en Cool, + siempre devuelve Int si es vÃ¡lido

@dataclass
class Resta(OperacionBinaria):
    operando: str = '-'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_sub\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Multiplicacion(OperacionBinaria):
    operando: str = '*'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_mul\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado



@dataclass
class Division(OperacionBinaria):
    operando: str = '/'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_divide\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Menor(OperacionBinaria):
    operando: str = '<'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_lt\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, ambito):
        self.izquierda.Tipo(ambito)
        self.derecha.Tipo(ambito)
        self.cast = 'Bool'

@dataclass
class LeIgual(OperacionBinaria):
    operando: str = '<='

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_leq\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado

    def Tipo(self, ambito):
        self.izquierda.Tipo(ambito)
        self.derecha.Tipo(ambito)
        self.cast = 'Bool'


@dataclass
class Igual(OperacionBinaria):
    operando: str = '='

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_eq\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    def valor(self, ambito):
        izq = self.izquierda.valor(ambito)
        dcha = self.derecha.valor(ambito)
        if izq == dcha:
            return True
        else:
            return False
    def Tipo(self, ambito):
        self.izquierda.Tipo(ambito)
        self.derecha.Tipo(ambito)

        tipo_izq = self.izquierda.cast
        tipo_der = self.derecha.cast

        tipos_basicos = ['Int', 'Bool', 'String']

        if tipo_izq in tipos_basicos or tipo_der in tipos_basicos:
            errores_sem.append(
                f"{self.linea}: Illegal comparison with a basic type."
            )

        self.cast = 'Bool'

@dataclass
class Neg(Expresion):
    expr: Expresion = None
    operador: str = '~'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_neg\n'
        resultado += self.expr.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
        
    def Tipo(self, ambito):
        self.expr.Tipo(ambito)
        if self.expr.cast == 'Int':
             self.cast = 'Int'
        else:
             self.cast = 'Object'


@dataclass
class Not(Expresion):
    expr: Expresion = None
    operador: str = 'NOT'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_comp\n'
        resultado += self.expr.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def Tipo(self, ambito):
        self.expr.Tipo(ambito)
        self.cast = 'Bool'


@dataclass
class EsNulo(Expresion):
    expr: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_isvoid\n'
        resultado += self.expr.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado

@dataclass
class Objeto(Expresion):
    nombre: str = '_no_set'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_object\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado

    def Tipo(self, ambito):
        #print(f"Analizando objeto {self.nombre} en el Ã¡mbito actual. Variables disponibles: {ambito.variables}. {ambito.get_tipo_variable(self.nombre)}")
        if ambito.get_tipo_variable(self.nombre) is None and self.nombre != 'self':
            errores_sem.append(f"{self.linea}: Undeclared identifier {self.nombre}.")
        elif self.nombre == 'self':
            self.cast = 'SELF_TYPE'
        else:
            self.cast = ambito.get_tipo_variable(self.nombre)

@dataclass
class NoExpr(Expresion):
    nombre: str = ''

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_no_expr\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Entero(Expresion):
    valor: int = 0

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_int\n'
        resultado += f'{(n+2)*" "}{self.valor}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    def Tipo(self, ambito):
        self.cast = 'Int'

@dataclass
class String(Expresion):
    valor: str = '_no_set'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_string\n'
        resultado += f'{(n+2)*" "}{self.valor}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    def Tipo(self, ambito):
        self.cast = 'String'
    


@dataclass
class Booleano(Expresion):
    valor: bool = False

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_bool\n'
        resultado += f'{(n+2)*" "}{1 if self.valor else 0}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    
    def valor(self, ambito):
        return self.valor
    
    def Tipo(self, ambito):
        self.cast = 'Bool'

@dataclass
class IterableNodo(Nodo):
    secuencia: List = field(default_factory=List)

@dataclass
class Programa(IterableNodo):
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{" "*n}_program\n'
        resultado += ''.join([c.str(n+2) for c in self.secuencia])
        return resultado

    def Tipo(self):
        errores_sem.clear()
        Ambito.clases = {}
        Ambito.clases_por_nombre = {}
        Ambito.arbol_herencias = {}

        ambito = Ambito()
        ambito.add_metodo('abort', Metodo(nombre='abort', tipo='Object'))
        ambito.add_metodo('type_name', Metodo(nombre='type_name', tipo='String'))
        ambito.add_metodo('copy', Metodo(nombre='copy', tipo='SELF_TYPE'))
        ambito.add_metodo('length', Metodo(nombre='length', tipo='Int'))

        for clase in self.secuencia:
            if clase.nombre in CLASES_BASICAS:
                add_error(
                    f"{clase.linea}: Redefinition of basic class {clase.nombre}."
                )
            else:
                ambito.registrar_clase(clase.nombre, clase)

        for clase in self.secuencia:
            ambito.anhadir_clase(clase, clase.padre)

        if 'Main' not in Ambito.clases_por_nombre:
            errores_sem.append("Class Main is not defined.")

        for clase in self.secuencia:
            clase.Tipo(ambito)
        for clase in self.secuencia:
            clase.load()

@dataclass
class Caracteristica(Nodo):
    nombre: str = '_no_set'
    tipo: str = '_no_set'
    cuerpo: Expresion = None

    def Tipo(self, ambito: Ambito):
        pass

@dataclass
class Clase(Nodo):
    nombre: str = '_no_set'
    padre: str = '_no_set'
    ambito: Optional[Ambito] = None
    nombre_fichero: str = '_no_set'
    caracteristicas: List[Caracteristica] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_class\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n+2)*" "}{self.padre}\n'
        resultado += f'{(n+2)*" "}"{self.nombre_fichero}"\n'
        resultado += f'{(n+2)*" "}(\n'
        resultado += ''.join([c.str(n+2) for c in self.caracteristicas])
        resultado += '\n'
        resultado += f'{(n+2)*" "})\n'
        return resultado
    
    def Tipo(self, ambito: Ambito):
        if self.padre != 'Object':
            ambito_class = ambito.get_ambito_clase(self.padre)
        else:
            ambito_class = ambito
        if ambito_class is None:
            raise Exception(f"Clase padre {self.padre} no encontrada para la clase {self.nombre} en el fichero {self.nombre_fichero}")
        self.ambito = Ambito(padre=ambito_class)
        self.ambito.tipo_clase_actual = self.nombre
        for caracteristica in self.caracteristicas:
            if isinstance(caracteristica, Metodo):
                self.ambito.add_metodo(caracteristica.nombre, caracteristica)
        ambito.set_ambito_clase(self.nombre, self.ambito)
        
    def load(self):
        if self.ambito is not None:
            for caracteristica in self.caracteristicas:
                caracteristica.Tipo(self.ambito)

@dataclass
class Metodo(Caracteristica):
    formales: List[Formal] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_method\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += ''.join([c.str(n+2) for c in self.formales])
        resultado += f'{(n + 2) * " "}{self.tipo}\n'
        resultado += self.cuerpo.str(n+2)

        return resultado
    
    def Tipo(self, ambito: Ambito):
        ambito_m = ambito.entrar_ambito()

        for formal in self.formales:
            formal.Tipo(ambito_m)

        ambito_m.add_metodo(self.nombre, self)
        if self.tipo not in ambito_m.clases_por_nombre and self.tipo not in CLASES_BASICAS:
            errores_sem.append(
                f"{self.linea}: Undefined return type {self.tipo} in method {self.nombre}."
            )
        self.cuerpo.Tipo(ambito_m)

        if not ambito_m.es_subtipo(self.cuerpo.cast, self.tipo) and self.cuerpo.cast != 'SELF_TYPE':
            errores_sem.append(
                    f"{self.linea}: Inferred return type {self.cuerpo.cast} of method {self.nombre} does not conform to declared return type {self.tipo}."
                )

        ambito.salir_ambito()


class Atributo(Caracteristica):

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_attr\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += self.cuerpo.str(n+2)
        return resultado
    
    def Tipo(self, ambito: Ambito):
        if self.nombre == "self":
            errores_sem.append(f"{self.linea}: 'self' cannot be the name of an attribute.")
            return

        padre = ambito.padre
        while padre:
            if self.nombre in padre.variables:
                errores_sem.append(
                    f"{self.linea}: Attribute {self.nombre} is an attribute of an inherited class."
                )
                break
            padre = padre.padre

        self.cuerpo.Tipo(ambito)
        ambito.add_variable(self.nombre, self.tipo)