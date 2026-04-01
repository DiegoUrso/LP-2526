# coding: utf-8

from Lexer import CoolLexer
from sly import Parser
import sys
import os
from Clases import *

class CoolParser(Parser):
    nombre_fichero = ''
    tokens = CoolLexer.tokens
    debugfile = "salida.out"
    errores = []

    @_("Clase", "Clase Programa")
    def Programa(self, p):
        if hasattr(p, 'Programa'):
            return Programa(secuencia=[p.Clase] + p.Programa.secuencia)
        else:
            return Programa(secuencia=[p.Clase])
    
    @_("CLASS TYPEID hereda '{' serie_atr_met '}' ';'") 
    def Clase(self, p):
        return Clase(nombre=p.TYPEID, padre=p.hereda, caracteristicas=p.serie_atr_met, nombre_fichero=self.nombre_fichero)

    @_("", "INHERITS TYPEID")
    def hereda(self, p):
        if hasattr(p, 'TYPEID'):
            return p.TYPEID
        else:
            return "Object"
    
    @_("", "atributo", "metodo", "serie_atr_met atributo", "serie_atr_met metodo")
    def serie_atr_met(self, p):
        if len(p) == 0:
            return []
        elif len(p) == 1:
            if hasattr(p, "atributo"):
                return [p.atributo]
            else:
                return [p.metodo]
        elif hasattr(p, "atributo"):
            return p.serie_atr_met + [p.atributo]
        else:
            return p.serie_atr_met + [p.metodo]
        
    @_("OBJECTID ':' TYPEID ';'", "OBJECTID ':' TYPEID ASSIGN expr ';'")
    def atributo(self, p):
        if hasattr(p, 'expr'):
            return Atributo(nombre=p.OBJECTID, tipo=p.TYPEID, cuerpo=p.expr)
        else:
            return Atributo(nombre=p.OBJECTID, tipo=p.TYPEID, cuerpo=NoExpr())
    
    @_("OBJECTID '(' ')' ':' TYPEID '{' expr '}' ';'", "OBJECTID '(' lista_formales ')' ':' TYPEID '{' expr '}' ';'", "OBJECTID '(' ')' ':' TYPEID '{' error '}' ';'", "OBJECTID '(' lista_formales ')' ':' TYPEID '{' error '}' ';'")
    def metodo(self, p):
        return Metodo(nombre=p.OBJECTID, formales=p.lista_formales if hasattr(p, 'lista_formales') else [], tipo=p.TYPEID, cuerpo=p.expr if hasattr(p, 'expr') else NoExpr())
    
    @_("formal", "formal ',' lista_formales")
    def lista_formales(self, p):
        return [p.formal] if not hasattr(p, 'lista_formales') else [p.formal] + p.lista_formales
    
    @_("OBJECTID ':' TYPEID")
    def formal(self, p):
        return Formal(nombre_variable=p.OBJECTID, tipo=p.TYPEID)
    
    @_("OBJECTID ASSIGN expr")
    def expr(self, p):
        return Asignacion(nombre=p.OBJECTID, cuerpo=p.expr)
    
    precedence = (
        ('right', 'ASSIGN'),
        ('right', 'NOT'),
        ('nonassoc', '<', 'LE', '='),
        ('left', '+', '-'),
        ('left', '*', '/'),
        ('right', 'ISVOID'),
        ('right', '~'),
        ('left', '@'),
        ('left', '.'),
    )

    @_("expr '+' expr")
    def expr(self, p):
        return Suma(izquierda=p.expr0, derecha=p.expr1)

    @_("expr '-' expr")
    def expr(self, p):
        return Resta(izquierda=p.expr0, derecha=p.expr1)

    @_("expr '*' expr")
    def expr(self, p):
        return Multiplicacion(izquierda=p.expr0, derecha=p.expr1)

    @_("expr '/' expr")
    def expr(self, p):
        return Division(izquierda=p.expr0, derecha=p.expr1)    
    
    @_("expr '<' expr")
    def expr(self, p):
        return Menor(izquierda=p.expr0, derecha=p.expr1)
    
    @_("expr LE expr")
    def expr(self, p):
        return LeIgual(izquierda=p.expr0, derecha=p.expr1)
    
    @_("expr '=' expr")
    def expr(self, p):
        return Igual(izquierda=p.expr0, derecha=p.expr1)
    
    @_("'(' expr ')'")
    def expr(self, p):
        return p.expr
    
    @_("NOT expr")
    def expr(self, p):
        return Not(expr=p.expr)
    
    @_("ISVOID expr")
    def expr(self, p):
        return EsNulo(expr=p.expr)
    
    @_("'~' expr")
    def expr(self, p):
        return Neg(expr=p.expr)
    
    @_("expr '@' TYPEID '.' OBJECTID '(' ')'", "expr '@' TYPEID '.' OBJECTID '(' lista_exprs ')'")
    def expr(self, p):
        return LlamadaMetodoEstatico(cuerpo=p.expr, clase=p.TYPEID, nombre_metodo=p.OBJECTID, argumentos=p.lista_exprs if hasattr(p, 'lista_exprs') else [])
    
    @_("expr '.' OBJECTID '(' ')'", "expr '.' OBJECTID '(' lista_exprs ')'", "OBJECTID '(' ')'","OBJECTID '(' lista_exprs ')'")
    def expr(self, p):
        if hasattr(p, 'expr'):
            return LlamadaMetodo(cuerpo=p.expr, nombre_metodo=p.OBJECTID, argumentos=p.lista_exprs if hasattr(p, 'lista_exprs') else [])
        else:
            return LlamadaMetodo(cuerpo=Objeto(nombre='self'), nombre_metodo=p.OBJECTID, argumentos=p.lista_exprs if hasattr(p, 'lista_exprs') else [])
        
    @_("expr", "expr ',' lista_exprs")
    def lista_exprs(self, p):
        return [p.expr] if not hasattr(p, 'lista_exprs') else [p.expr] + p.lista_exprs
    
    @_("IF expr THEN expr ELSE expr FI")
    def expr(self, p):
        return Condicional(condicion=p.expr0, verdadero=p.expr1, falso=p.expr2)
    
    @_("WHILE expr LOOP expr POOL")
    def expr(self, p):
        return Bucle(condicion=p.expr0, cuerpo=p.expr1)
    
    @_("LET OBJECTID ':' TYPEID IN expr",
       "LET OBJECTID ':' TYPEID ASSIGN expr IN expr",
       "LET OBJECTID ':' TYPEID lista_let IN expr",
       "LET OBJECTID ':' TYPEID ASSIGN expr lista_let IN expr")
    def expr(self, p):
        if len(p) == 6: # Without ASSIGN expr, without lista_let
            return Let(nombre=p.OBJECTID, tipo=p.TYPEID, inicializacion=NoExpr(), cuerpo=p.expr)
        elif len(p) == 8: # With ASSIGN expr, without lista_let
            return Let(nombre=p.OBJECTID, tipo=p.TYPEID, inicializacion=p.expr0, cuerpo=p.expr1)
        elif len(p) == 7: # Without ASSIGN expr, with lista_let
            temp = Let()
            for i, (name, type, init) in enumerate(reversed(p.lista_let)):
                if i == 0:
                    temp = Let(nombre=name, tipo=type, inicializacion=init, cuerpo=p.expr)
                else:
                    temp = Let(nombre=name, tipo=type, inicializacion=init, cuerpo=temp)
            return Let(nombre=p.OBJECTID, tipo=p.TYPEID, inicializacion=NoExpr(), cuerpo=temp)
        elif len(p) == 9: # With ASSIGN expr, with lista_let
            temp = Let()
            for i, (name, type, init) in enumerate(reversed(p.lista_let)):
                if i == 0:
                    temp = Let(nombre=name, tipo=type, inicializacion=init, cuerpo=p.expr1)
                else:
                    temp = Let(nombre=name, tipo=type, inicializacion=init, cuerpo=temp)
            return Let(nombre=p.OBJECTID, tipo=p.TYPEID, inicializacion=p.expr0, cuerpo=temp)

    @_("let_item", "let_item lista_let")
    def lista_let(self, p):
        return [p.let_item] if not hasattr(p, 'lista_let') else [p.let_item] + p.lista_let
    
    @_("',' OBJECTID : TYPEID", "',' OBJECTID ':' TYPEID ASSIGN expr", "error ',' OBJECTID ':' TYPEID", "error , OBJECTID ':' TYPEID ASSIGN expr")
    def let_item(self, p):
        return (p.OBJECTID, p.TYPEID, p.expr) if hasattr(p, 'expr') else (p.OBJECTID, p.TYPEID, NoExpr())

    @_("CASE expr OF esac_list ESAC")
    def expr(self, p):
        return Swicht(expr=p.expr, casos=p.esac_list)
    
    @_("OBJECTID ':' TYPEID DARROW expr ';'", "OBJECTID ':' TYPEID DARROW expr ';' esac_list")
    def esac_list(self, p):
        return [RamaCase(nombre_variable=p.OBJECTID, tipo=p.TYPEID, cuerpo=p.expr)] if not hasattr(p, 'esac_list') else [RamaCase(nombre_variable=p.OBJECTID, tipo=p.TYPEID, cuerpo=p.expr)] + p.esac_list
        
    @_("NEW TYPEID")
    def expr(self, p):
        return Nueva(tipo=p.TYPEID)
    
    @_("'{' bloque_exprs '}'")
    def expr(self, p):
        return Bloque(expresiones=p.bloque_exprs)
    
    @_("expr ';'", "expr ';' bloque_exprs", "expr ';' error ';' bloque_exprs")
    def bloque_exprs(self, p):
        return [p.expr] if not hasattr(p, 'bloque_exprs') else [p.expr] + p.bloque_exprs
    
    @_("OBJECTID")
    def expr(self, p):
        return Objeto(nombre=p.OBJECTID)
    
    @_("INT_CONST")
    def expr(self, p):
        return Entero(valor=p.INT_CONST)
    
    @_("STR_CONST")
    def expr(self, p):
        return String(valor=p.STR_CONST)
    
    @_("BOOL_CONST")
    def expr(self, p):
        return Booleano(valor=p.BOOL_CONST)
    
    def error(self, p):
        #print(p)
        if p:
            if p.type in ('TYPEID', 'OBJECTID', 'INT_CONST', 'STR_CONST', 'BOOL_CONST'):
                source = f"{p.type} = {p.value}"
            elif p.type == p.value:
                source = f"'{p.type}'"
            else:
                source = p.type
            self.errores.append(f"\"{self.nombre_fichero}\", line {p.lineno}: syntax error at or near {source}")
        else:
            self.errores.append(f"\"{self.nombre_fichero}\", line 0: syntax error at or near EOF")
        
        #print(self.errores)

    #def errok(self):
    #    '''Redefinición de la función que limpia el registro de errores'''
    #    self.errorok = False
