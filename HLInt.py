import sys
import os
import re

# ==========================================
# BENITEZ: FILE I/O & WHITESPACE REMOVAL
# ==========================================
def remove_spaces(source_text: str, output_path: str = "NOSPACES.TXT") -> str:
    """
    Removes all spaces from the source code and writes the result to NOSPACES.TXT.
    """
    # Remove all space characters (' ') while keeping newlines for tokenization
    nospaces_content = source_text.replace(" ", "")
    with open(output_path, "w") as f:
        f.write(nospaces_content)
    return nospaces_content


# ==========================================
# ADVINCULA: TOKENIZER & SYMBOLS EXTRACTION
# ==========================================
# Reserved keywords and recognized symbols from the HL specification
RESERVED_WORDS = {"integer", "double", "output", "if"}
SYMBOLS = [":=", "==", "!=", "<<", ":", "=", "+", "-", ";", "(", ")", ">", "<", '"']

def extract_reserved_and_symbols(source_text: str, output_path: str = "RES_SYM.TXT") -> list:
    """
    Scans the source code, identifies reserved keywords and symbols,
    and writes them in order to RES_SYM.TXT.
    """
    # Token specification pattern
    token_pattern = re.compile(
        r'(?P<SYMBOL>:=|==|!=|<<|[:=+;\(\)<>"-])|'
        r'(?P<WORD>[a-zA-Z_][a-zA-Z0-9_]*)|'
        r'(?P<NUMBER>\d+(\.\d+)?)|'
        r'(?P<SKIP>\s+)'
    )

    found_res_sym = []
    tokens = []

    for match in token_pattern.finditer(source_text):
        kind = match.lastgroup
        val = match.group(kind)
        
        if kind == 'SKIP':
            continue
        elif kind == 'SYMBOL':
            found_res_sym.append(val)
            tokens.append((kind, val))
        elif kind == 'WORD':
            val_lower = val.lower()
            if val_lower in RESERVED_WORDS:
                found_res_sym.append(val_lower)
                tokens.append(('KEYWORD', val_lower))
            else:
                tokens.append(('IDENT', val))
        elif kind == 'NUMBER':
            tokens.append(('NUMBER', val))

    # Write reserved words and symbols to file
    with open(output_path, "w") as f:
        for item in found_res_sym:
            f.write(f"{item}\n")

    return tokens


# ==========================================
# ROBLES: SYNTAX VALIDATOR & GRAMMAR CHECK
# ==========================================
class HLParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def match(self, expected_type, expected_val=None):
        tok = self.current_token()
        if not tok:
            return False
        kind, val = tok
        if kind == expected_type:
            if expected_val is None or val == expected_val:
                self.pos += 1
                return True
        return False

    def parse_program(self) -> bool:
        """
        Validates the complete program statement by statement.
        """
        if not self.tokens:
            return False
        
        while self.pos < len(self.tokens):
            if not self.parse_statement():
                return False
        return True

    def parse_statement(self) -> bool:
        tok = self.current_token()
        if not tok:
            return False
        kind, val = tok

        # 1. Output statement: output << (<string> | <expr>);
        if kind == 'KEYWORD' and val == 'output':
            self.pos += 1
            if not self.match('SYMBOL', '<<'):
                return False
            
            # String literal: " <string> "
            if self.match('SYMBOL', '"'):
                # Read string contents until closing quote
                while self.pos < len(self.tokens) and not self.match('SYMBOL', '"'):
                    self.pos += 1
            else:
                # Value or expression
                if not self.parse_expression():
                    return False
            return self.match('SYMBOL', ';')

        # 2. Conditional statement: if ( <condition> ) <statement>
        elif kind == 'KEYWORD' and val == 'if':
            self.pos += 1
            if not self.match('SYMBOL', '('):
                return False
            if not self.parse_condition():
                return False
            if not self.match('SYMBOL', ')'):
                return False
            return self.parse_statement()

        # 3. Variable declaration or Assignment
        elif kind == 'IDENT':
            self.pos += 1
            next_tok = self.current_token()
            if not next_tok:
                return False

            # Variable declaration: x: integer; or y: double;
            if next_tok[1] == ':':
                self.pos += 1
                type_tok = self.current_token()
                if type_tok and type_tok[0] == 'KEYWORD' and type_tok[1] in ('integer', 'double'):
                    self.pos += 1
                    return self.match('SYMBOL', ';')
                return False

            # Assignment: x:= 5; (literal assignment)
            elif next_tok[1] == ':=':
                self.pos += 1
                if not self.parse_literal():
                    return False
                return self.match('SYMBOL', ';')

            # Mathematical assignment: x = 3 + 2;
            elif next_tok[1] == '=':
                self.pos += 1
                if not self.parse_expression():
                    return False
                return self.match('SYMBOL', ';')

            return False

        return False

    def parse_condition(self) -> bool:
        """
        Parses condition with relational operators: >, <, ==, !=
        """
        if not self.parse_operand():
            return False
        
        tok = self.current_token()
        if tok and tok[1] in ('>', '<', '==', '!='):
            self.pos += 1
            return self.parse_operand()
        return False

    def parse_operand(self) -> bool:
        tok = self.current_token()
        if not tok:
            return False
        if tok[0] in ('IDENT', 'NUMBER'):
            self.pos += 1
            return True
        return False

    def parse_literal(self) -> bool:
        tok = self.current_token()
        if tok and tok[0] == 'NUMBER':
            # Check precision rules: single digit integer OR 2-decimal double
            val = tok[1]
            if '.' in val:
                decimals = val.split('.')[1]
                if len(decimals) != 2:
                    return False
            else:
                if len(val) != 1:
                    return False
            self.pos += 1
            return True
        return False

    def parse_expression(self) -> bool:
        """
        Parses operands with optional + or - operations.
        """
        if not self.parse_operand():
            return False
        
        tok = self.current_token()
        if tok and tok[1] in ('+', '-'):
            self.pos += 1
            return self.parse_operand()
        return True


# ==========================================
# MAIN DRIVER
# ==========================================
def main():
    if len(sys.argv) < 2:
        print("Usage: python HLInt.py <source_file.HL>")
        return

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    with open(input_file, "r") as f:
        source_code = f.read()

    # Step 1: Remove spaces and write NOSPACES.TXT
    remove_spaces(source_code, "NOSPACES.TXT")

    # Step 2: Extract reserved words and symbols into RES_SYM.TXT
    tokens = extract_reserved_and_symbols(source_code, "RES_SYM.TXT")

    # Step 3: Syntax error checking
    parser = HLParser(tokens)
    is_valid = parser.parse_program()

    # Step 4: Screen Output
    if is_valid:
        print("NO ERROR(S) FOUND")
    else:
        print("ERROR")


if __name__ == "__main__":
    main()