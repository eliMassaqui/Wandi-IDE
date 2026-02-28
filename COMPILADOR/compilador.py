import ast

class compiladorWandi:
    def __init__(self):
        self.libraries = set()
        self.objects = set()
        self.globals = []
        self.variables_declared = set()

        # Mapeamento inspirado na estrutura lógica do Arduino (Wiring)
        self.HARDWARE_MAP = {
            "pinMode": "pinMode({0}, {1});",
            "digitalWrite": "digitalWrite({0}, {1});",
            "digitalRead": "digitalRead({0})",
            "analogRead": "analogRead({0})",
            "analogWrite": "analogWrite({0}, {1});",
            "delay": "delay({0});",
            "print": "Serial.print({0});",       # Lógica Arduino: Não pula linha
            "println": "Serial.println({0});",   # Lógica Arduino: Pula linha
            "Serial_begin": "Serial.begin({0});",
            "Serial_available": "Serial.available()",
            "Serial_read": "Serial.read()"
        }

    def _get_value(self, node):
        """Converte nós Python em sintaxe C++ para o Arduino"""
        if node is None: return "0"
        
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str): return f'"{node.value}"'
            return str(node.value)
            
        elif isinstance(node, ast.Name):
            # Converte Booleanos Python para C++
            if node.id == "True": return "true"
            if node.id == "False": return "false"
            return node.id
            
        elif isinstance(node, ast.BinOp):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            ops = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}
            return f"{left} {ops[type(node.op)]} {right}"
            
        elif isinstance(node, ast.Compare):
            left = self._get_value(node.left)
            op = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", 
                  ast.Gt: ">", ast.GtE: ">="}[type(node.ops[0])]
            right = self._get_value(node.comparators[0])
            return f"{left} {op} {right}"

        elif isinstance(node, ast.Call):
            args = [self._get_value(a) for a in node.args]
            # Caso: analogRead(0)
            if isinstance(node.func, ast.Name):
                name = node.func.id
                if name in self.HARDWARE_MAP:
                    return self.HARDWARE_MAP[name].replace(";", "").format(*args)
            # Caso: servo.read()
            elif isinstance(node.func, ast.Attribute):
                obj = node.func.value.id
                attr = node.func.attr
                return f"{obj}.{attr}({', '.join(args)})"
                
        return "0"

    def _parse_body(self, body, indent=2):
        lines = []
        space = " " * indent
        for node in body:
            # --- ESTRUTURAS DE CONTROLE (IF/WHILE) ---
            if isinstance(node, (ast.If, ast.While)):
                keyword = "if" if isinstance(node, ast.If) else "while"
                cond = self._get_value(node.test)
                lines.append(f"{space}{keyword} ({cond}) {{")
                lines.extend(self._parse_body(node.body, indent + 2))
                lines.append(f"{space}}}")
                if isinstance(node, ast.If) and node.orelse:
                    lines.append(f"{space}else {{")
                    lines.extend(self._parse_body(node.orelse, indent + 2))
                    lines.append(f"{space}}}")

            # --- ATRIBUIÇÃO DE VARIÁVEIS ---
            elif isinstance(node, ast.Assign):
                target = node.targets[0].id
                value = self._get_value(node.value)
                if target not in self.variables_declared:
                    # Define tipo: float se tiver ponto ou for leitura analógica, senão int
                    tipo = "float" if "." in value or "Read" in value else "int"
                    self.variables_declared.add(target)
                    lines.append(f"{space}{tipo} {target} = {value};")
                else:
                    lines.append(f"{space}{target} = {value};")

            # --- COMANDOS E PROCEDIMENTOS ---
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                args = [self._get_value(a) for a in call.args]

                # Métodos de Objetos (ex: servo.attach)
                if isinstance(call.func, ast.Attribute):
                    obj = call.func.value.id
                    attr = call.func.attr
                    if obj == "servo": self.objects.add(f"Servo {obj};")
                    lines.append(f"{space}{obj}.{attr}({', '.join(args)});")
                
                # Funções Globais (ex: print, delay)
                elif isinstance(call.func, ast.Name):
                    name = call.func.id
                    if name in self.HARDWARE_MAP:
                        # Se usar print("Texto", variavel) no estilo Python, 
                        # o compilador gera Serial.print() + Serial.println()
                        if name in ["print", "println"] and len(args) > 1:
                            lines.append(f"{space}Serial.print({args[0]});")
                            lines.append(f"{space}Serial.println({args[1]});")
                        else:
                            lines.append(f"{space}{self.HARDWARE_MAP[name].format(*args)}")
        return lines

    def translate(self, py_code: str) -> str:
        try:
            tree = ast.parse(py_code)
            self.libraries, self.objects, self.globals, self.variables_declared = set(), set(), [], set()
            functions = []

            for node in tree.body:
                # 1. Imports -> #include
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if n.name == "servo": self.libraries.add("#include <Servo.h>")
                
                # 2. Globais
                elif isinstance(node, ast.Assign):
                    target = node.targets[0].id
                    val = self._get_value(node.value)
                    tipo = "float" if "." in val else "int"
                    self.variables_declared.add(target)
                    self.globals.append(f"{tipo} {target} = {val};")

                # 3. Funções (setup e loop)
                elif isinstance(node, ast.FunctionDef):
                    body = self._parse_body(node.body)
                    functions.append(f"void {node.name}() {{\n" + "\n".join(body) + "\n}")

            # Montagem do Código Final
            res = ["// --- WANDI ENGINE (HYBRID WIRING) ---", ""]
            res.extend(sorted(list(self.libraries)))
            res.extend(sorted(list(self.objects)))
            res.append("")
            res.extend(self.globals)
            res.append("")
            res.extend(functions)
            
            return "\n".join(res)
        except Exception as e:
            return f"// ERRO CRÍTICO NO TRADUTOR: {e}"