# coding: utf-8
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Optional

errores_sem = []

CLASES_BASICAS = {"Object", "Int", "Bool", "String"}

def add_error(msg):
    if msg not in errores_sem:
        errores_sem.append(msg)

class Ambito:
    clases: dict[str, 'Ambito'] = {}
    ambitos: List['Ambito'] = []
    arbol_clases: dict[str, 'Clase'] = {}
    clases_por_nombre: dict[str, 'Clase'] = {}
    lista_metodos: dict['Clase', 'Metodo'] = {}

    def __init__(self, padre: Optional['Ambito'] = None):
        self.padre = padre
        self.variables: dict[str, str] = {}
        self.metodos: dict[str, Metodo] = {}
        
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

    def anhadir_clase_arbol(self, clase, padre):
        Ambito.arbol_clases[clase.nombre] = padre
        cars_padre: dict[str, 'Caracteristica'] = {}

        if padre != 'Object':
            for c in self.clases_por_nombre.get(padre, Clase()).caracteristicas:
                cars_padre[c.nombre] = c
            for caracteristica in clase.caracteristicas:
                if isinstance(caracteristica, Metodo):
                    self.add_metodo(caracteristica.nombre, caracteristica)
                    if caracteristica.nombre in cars_padre:
                        car_padre = cars_padre[caracteristica.nombre]
                        for formal in caracteristica.formales:
                            for f in car_padre.formales:
                                if formal.nombre_variable == f.nombre_variable and formal.tipo != f.tipo:
                                    errores_sem.append(f"{caracteristica.linea}: In redefined method {caracteristica.nombre}, parameter type {formal.tipo} is different from original type {f.tipo}")

    def get_ambito_clase(self, nombre: str) -> Optional['Ambito']:
        if nombre in Ambito.clases:
            return Ambito.clases[nombre]
        else:
            return None
        
    def add_clase(self, nombre: str, ambito: 'Ambito'):
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
    
    def es_subtipo(self, tipo1: Optional[str], tipo2: Optional[str]) -> bool:
        if tipo1 is None or tipo2 is None:
            return False
        if tipo1 == tipo2:
            return True
        elif tipo1 == 'Object':
            return True
        elif tipo1 == 'Int' and tipo2 == 'Object':
            return True
        elif tipo1 == 'String' and tipo2 == 'Object':
            return True
        elif tipo1 == 'Bool' and tipo2 == 'Object':
            return True
        else:
            return False

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
        else:
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
        clase = ambito.get_ambito_clase(self.clase)
        if clase is None:
            metodo = ambito.get_metodo(self.nombre_metodo)
        else:
            metodo = clase.get_metodo(self.nombre_metodo)
        if metodo is None or metodo.tipo == 'SELF_TYPE':
            self.cast = self.cuerpo.cast
        else:
            self.cast = metodo.tipo
        #print(f"Analizando llamada a método estático {self.nombre_metodo} con cuerpo {self.cuerpo} del tipo {self.cuerpo.cast} y clase {self.clase}. El tipo resultante es {self.cast}")


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

        while clase_nombre is not None and metodo is None:
            clase = Ambito.clases_por_nombre.get(clase_nombre)
            if clase:
                metodo = clase.get_metodo(self.nombre_metodo)
                clase_nombre = Ambito.arbol_clases.get(clase_nombre)
            else:
                break

        if metodo is None:
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

        # 🔴 CHECK IMPORTANTE (ESTO ES LO QUE TE FALTA)
        if self.inicializacion.cast != '_no_type' and self.tipo != '_no_set':
            if not ambito.es_subtipo(self.inicializacion.cast, self.tipo):
                errores_sem.append(
                    f"{self.linea}: Inferred type {self.inicializacion.cast} of initialization of {self.nombre} does not conform to declared type {self.tipo}."
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

        self.cast = 'Int'  # en Cool, + siempre devuelve Int si es válido

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
        #print(f"Analizando objeto {self.nombre} en el ámbito actual. Variables disponibles: {ambito.variables}. {ambito.get_tipo_variable(self.nombre)}")
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
        Ambito.clases = {}
        Ambito.clases_por_nombre = {}
        Ambito.arbol_clases = {}

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
            ambito.anhadir_clase_arbol(clase, clase.padre)

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
        self.new_ambito = Ambito(padre=ambito_class)
        self.new_ambito.tipo_clase_actual = self.nombre
        for caracteristica in self.caracteristicas:
            if isinstance(caracteristica, Metodo):
                self.new_ambito.add_metodo(caracteristica.nombre, caracteristica)
        ambito.add_clase(self.nombre, self.new_ambito)
        
    def load(self):
        for caracteristica in self.caracteristicas:
            caracteristica.Tipo(self.new_ambito)

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
        if self.tipo not in Ambito.clases_por_nombre and self.tipo not in CLASES_BASICAS:
            errores_sem.append(
                f"{self.linea}: Undefined return type {self.tipo} in method {self.nombre}."
            )
        self.cuerpo.Tipo(ambito_m)
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