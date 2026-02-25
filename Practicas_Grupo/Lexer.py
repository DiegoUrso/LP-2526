# coding: utf-8

from sly import Lexer
class Comentario(Lexer):
    tokens = {ERROR}
    
    def nesting(self, change = 0):
        if not hasattr(self, 'nesting_level'):
            self.nesting_level = 1
        self.nesting_level += change
        if self.nesting_level < 0:
            self.nesting_level = 0
        return self.nesting_level
    
    @_(r'.\Z|\r?\n\Z')
    def EOF(self, t):
        t.type = 'ERROR'
        t.value = '"EOF in comment"'
        self.nesting_level = 1
        self.begin(CoolLexer)
        return t
    @_(r'(?<!\\)\(\*')
    def OPEN(self, t):
        self.nesting(1)
    @_(r'(?<!\\)\*\)\Z')
    def CLOSE_EOF(self, t):
        if self.nesting(-1) > 0:
            t.type = 'ERROR'
            t.value = '"EOF in comment"'
            self.nesting_level = 1
            self.begin(CoolLexer)
            return t
    @_(r'(?<!\\)\*\)')
    def CLOSE(self, t):
        if self.nesting(-1) == 0:
            self.nesting_level = 1
            self.begin(CoolLexer)
    @_(r'\r?\n')
    def LINEA(self, t):
        self.lineno += 1
    @_(r'.')
    def PASAR(self, t):
        pass
class StringLexer(Lexer):
    tokens = {STR_CONST, ERROR}
    
    def count(self, n = 0):
        if not hasattr(self, 'counter'):
            self.counter = 0
        self.counter += n
        return self.counter
    def string(self, append = '', reset = False):
        if not hasattr(self, 'string_buffer'):
            self.string_buffer = ''
        if reset:
            self.string_buffer = ''
            self.counter = 0
        self.string_buffer += append
        return self.string_buffer

    @_(r'.+(?<!\\)\0.+?"|.+(?<!\\)\0.+')
    def NULL(self, t):
        t.type = "ERROR"
        t.value = '"String contains null character."'
        self.string(reset=True)
        self.begin(CoolLexer)
        return t
    @_(r'.+\\\0.+?"|.+\\\0.+')
    def ESCAPE_NULL(self, t):
        t.type = "ERROR"
        t.value = '"String contains escaped null character."'
        self.string(reset=True)
        self.begin(CoolLexer)
        return t
    @_(r'.+\Z|\\\r?\n\Z')
    def EOF(self, t):
        t.type = 'ERROR'
        t.value = '"EOF in string constant"'
        self.string(reset=True)
        self.begin(CoolLexer)
        return t
    @_(r'[^"\\]*\r?\n')
    def LINEBREAK(self, t):
        t.type = 'ERROR'
        t.value = '"Unterminated string constant"'
        self.string(reset=True)
        self.begin(CoolLexer)
        return t
    @_(r'[^\r\v\x1b\x0c\x12"\\]+') # Exclude control characters, double quotes, and backslashes
    def STR(self, t):
        self.string(t.value.encode('unicode_escape').decode('ascii'))
        self.count(len(t.value))
    @_(r'\\\r?\n')
    def ESCAPE_LINEA(self, t):
        self.string('\\n')
        self.count(1)
        self.lineno += 1
    @_(r'\\.')
    def ESCAPE(self, t):
        if t.value[1] in ['n', 't', 'f', 'b', '\\', '"']:
            self.string(t.value)
        elif t.value[1] == '\t':
            self.string('\\t')
        elif t.value[1] == '\b':
            self.string('\\b')
        elif t.value[1] == '\f':
            self.string('\\f')
        else:
            self.string(t.value[1])
        self.count(1)
    @_(r'"')
    def STR_CONST(self, t):
        if self.count() > 1024:
            t.type = 'ERROR'
            t.value = '"String constant too long"'
        else:
            t.value = f'"{self.string()}"' # TODO: Buscar mejor forma.
        self.string(reset=True)
        self.begin(CoolLexer)
        return t
    @_(r'.')
    def CHAR(self, t):
        # Special handling for control characters
        if t.value == '\r':
            self.string('\\015')
        elif t.value == '\x1b':
            self.string('\\033')
        elif t.value == '\v':
            self.string('\\013')
        elif t.value == '\x0c':
            self.string('\\f')
        elif t.value == '\x12':
            self.string('\\022')
        else:
            self.string(t.value)
        self.count(1)
        
class CoolLexer(Lexer):
    tokens = {OBJECTID, INT_CONST, BOOL_CONST, TYPEID,
              ELSE, IF, FI, THEN, NOT, IN, CASE, ESAC, CLASS,
              INHERITS, ISVOID, LET, LOOP, NEW, OF,
              POOL, THEN, WHILE, STR_CONST, LE, DARROW, ASSIGN}
    ignore = '\t \n\r\f\v'
    literals = {'.', '{', '}', '(', ')', ':', ';', ',', '+', '-', '*', '~', '<', '=', '/', '@'}
    invisibles = {chr(i) for i in range(32)} | {chr(127)}
    INT_CONST = r'[0-9]+'
    IF = r'\b[iI][fF]\b'
    FI = r'\b[fF][iI]\b'
    THEN = r'\b[tT][hH][eE][nN]\b'
    WHILE = r'\b[wW][hH][iI][lL][eE]\b'
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
    
    @_(r'\r?\n')
    def LINEBREAK(self, t):
        self.lineno += 1
    
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
        elif t.value in self.invisibles:
            octal_value = f"\\{ord(t.value):03o}"
            t.value = f'"{octal_value}"'
        else:
            escaped_value = t.value.replace('\\', '\\\\').replace('"', '\\"')
            t.value = f'"{escaped_value}"'
        return t
    
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
