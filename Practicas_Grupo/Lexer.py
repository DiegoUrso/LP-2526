# coding: utf-8

from sly import Lexer
import re
class Comentario(Lexer):
    tokens = {}
    
    def nesting(self, change = 0):
        if not hasattr(self, 'nesting_level'):
            self.nesting_level = 1
        self.nesting_level += change
        if self.nesting_level < 0:
            self.nesting_level = 0
        return self.nesting_level
    
    @_(r'\n|\r')
    def LINEA(self, t):
        self.lineno += 1
    @_(r'(?<!\\)\(\*')
    def OPEN(self, t):
        self.nesting(1)
    @_(r'(?<!\\)\*\)')
    def CLOSE(self, t):
        if self.nesting(-1) == 0:
            self.nesting_level = 1
            self.begin(CoolLexer)
    @_(r'.')
    def PASAR(self, t):
        pass
class StringLexer(Lexer):
    tokens = {STR_CONST, ERROR}
    
    def string(self, append = '', reset = False):
        if not hasattr(self, 'string_buffer'):
            self.string_buffer = ''
        if reset:
            self.string_buffer = ''
        self.string_buffer += append
        return self.string_buffer
    
    @_(r'[^"\\]*(\n|\r)')
    def LINEBREAK(self, t):
        t.type = 'ERROR'
        if '\0' in t.value:
            t.value = '"String contains null character."'
        else:
            t.value = '"Unterminated string constant"'
        self.string(reset=True)
        self.begin(CoolLexer)
        return t
    @_(r'[^"\\]+')
    def STR(self, t):
        self.string(t.value)
    @_(r'\\(\n|\r)')
    def ESCAPE_LINEA(self, t):
        self.string('\\n')
        self.lineno += 1
    @_(r'\\.')
    def ESCAPE(self, t):
        if t.value[1] in ['n', 't', 'f', 'b', '\\', '"']:
            self.string(t.value)
        else:
            self.string(t.value[1])
    @_(r'"')
    def STR_CONST(self, t):
        if '\0' in self.string():
            t.type = 'ERROR'
            if re.search(r'\\\0', self.string()):
                t.value = '"String contains escaped null character."'
            else:
                t.value = '"String contains null character."'
        else:
            t.value = f'"{self.string()}"'
        self.string(reset=True)
        self.begin(CoolLexer)
        return t
    
    ## TODO: EOF case
        
class CoolLexer(Lexer):
    tokens = {OBJECTID, INT_CONST, BOOL_CONST, TYPEID,
              ELSE, IF, FI, THEN, NOT, IN, CASE, ESAC, CLASS,
              INHERITS, ISVOID, LET, LOOP, NEW, OF,
              POOL, THEN, WHILE, STR_CONST, LE, DARROW, ASSIGN}
    ignore = '\t \n'
    literals = {'.', '{', '}', '(', ')', ':', ';', ',', '+', '-', '*', '~', '<', '>', '=', '/', '@'}
    IF = r'\b[iI][fF]\b'
    FI = r'\b[fF][iI]\b'
    THEN = r'\b[tT][hH][eE][nN]\b'
    NOT = r'\b[nN][oO][tT]\b'
    IN = r'\b[iI][nN]\b'
    CASE = r'\b[cC][aA][sS][eE]\b'
    ELSE = r'\b[eE][lL][sS][eE]\b'
    ESAC = r'\b[eE][sS][aA][cC]\b'
    CLASS = r'\b[cC][lL][aA][sS][sS]\b'
    INHERITS = r'\b[iI][nN][hH][eE][rR][iI][tT][sS]\b'
    ISVOID = r'\b[iI][sS][vV][oO][iI][dD]\b'
    LET = r'\b[lL][eE][tT]\b'
    LOOP = r'\b[lL][oO][oO][pP]\b'
    NEW = r'\b[nN][eE][wW]\b'
    OF = r'\b[oO][fF]\b'
    POOL = r'\b[pP][oO][oO][lL]\b'
    ASSIGN = r'<-'
    LE = r'<='
    DARROW = r'=>'
    
    @_(r'"')
    def STR_CONST(self, t):
        self.begin(StringLexer)
    
    @_(r'\bt[rR][uU][eE]\b|\bf[aA][lL][sS][eE]\b')
    def BOOL_CONST(self, t):
        t.value = t.value.lower() == 'true'
        return t
    
    @_(r'0|[1-9][0-9]*')
    def INT_CONST(self, t):
        t.value = int(t.value)
        return t
    
    @_(r'\n|\r')
    def LINEBREAK(self, t):
        self.lineno += 1
    
    @_(r'\b[wW][hH][iI][lL][eE]\b')
    def WHILE(self, t):
        t.value = (t.value) + 'dddd'
        return t
    
    @_(r'[a-z][A-Z0-9_a-z]*')
    def OBJECTID(self, t):
        return t
    
    @_(r'[A-Za-z0-9]\w*')
    def TYPEID(self, t):
        return t
    
    @_(r'\(\*')
    def IR(self, t):
        self.begin(Comentario)
        
    @_(r'--.*')
    def COMENTARIO(self, t):
        pass
    
    @_(r'\*\)|.')
    def ERROR(self, t):
        if t.value in self.literals:
            t.type = t.value
        elif t.value == "*)":
            t.value = f'"Unmatched *)"'
        else:
            t.value = f'"{t.value}"'
        return t

    def error(self, t):
        self.index += 1
    
    
    CARACTERES_CONTROL = [bytes.fromhex(i+hex(j)[-1]).decode('ascii')
                          for i in ['0', '1']
                          for j in range(16)] + [bytes.fromhex(hex(127)[-2:]).decode("ascii")]
    
    def error(self, t):
        self.index += 1
        
    def salida(self, texto):
        lexer = CoolLexer()
        list_strings = []
        for token in lexer.tokenize(texto):
            result = f'#{token.lineno} {token.type} '
            if token.type == 'OBJECTID':
                result += f"{token.value}"
            elif token.type == 'BOOL_CONST':
                result += "true" if token.value else "false"
            elif token.type == 'TYPEID':
                result += f"{str(token.value)}"
            elif token.type in self.literals:
                result = f'#{token.lineno} \'{token.type}\' '
            elif token.type == 'STR_CONST':
                result += token.value
            elif token.type == 'INT_CONST':
                result += str(token.value)
            elif token.type == 'ERROR':
                result = f'#{token.lineno} {token.type} {token.value}'
            else:
                result = f'#{token.lineno} {token.type}'
            list_strings.append(result)
        return list_strings
