import ast

class compiladorWandi:
    def __init__(self):
        self.libraries = set()
        self.objects = set()
        self.globals = []
        self.variables_declared = set()

        # Mapeamento de Comandos (Sintaxe Arduino)
        self.HARDWARE_MAP = {
            "pinMode": "pinMode({0}, {1});",
            "digitalWrite": "digitalWrite({0}, {1});",
            "digitalRead": "digitalRead({0})",
            "analogRead": "analogRead({0})",
            "analogWrite": "analogWrite({0}, {1});",
            "delay": "delay({0});",
            "print": "Serial.println({0});",
            "Serial_begin": "Serial.begin({0});"
        }

    def _get_value(self, node):
        """Converte nós Python em valores C++ (Pilar da Sequência)"""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str): return f'"{node.value}"'
            return str(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.BinOp):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            ops = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}
            return f"{left} {ops[type(node.op)]} {right}"
        elif isinstance(node, ast.Compare):
            left = self._get_value(node.left)
            op = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">="}[type(node.ops[0])]
            right = self._get_value(node.comparators[0])
            return f"{left} {op} {right}"
        return ""

    def _parse_body(self, body, indent=2):
        """Processa blocos de código (Decisão e Iteração)"""
        lines = []
        space = " " * indent
        for node in body:
            # --- DECISÃO ---
            if isinstance(node, ast.If):
                cond = self._get_value(node.test)
                lines.append(f"{space}if ({cond}) {{")
                lines.extend(self._parse_body(node.body, indent + 2))
                lines.append(f"{space}}}")
                if node.orelse:
                    lines.append(f"{space}else {{")
                    lines.extend(self._parse_body(node.orelse, indent + 2))
                    lines.append(f"{space}}}")

            # --- ITERAÇÃO ---
            elif isinstance(node, ast.While):
                cond = self._get_value(node.test).replace("True", "true")
                lines.append(f"{space}while ({cond}) {{")
                lines.extend(self._parse_body(node.body, indent + 2))
                lines.append(f"{space}}}")

            # --- ATRIBUIÇÃO ---
            elif isinstance(node, ast.Assign):
                target = node.targets[0].id
                value = self._get_value(node.value)
                # Se estiver dentro de uma função e não for global, precisa de tipo
                if target not in self.variables_declared:
                    tipo = "float" if "." in value else "int"
                    self.variables_declared.add(target)
                    lines.append(f"{space}{tipo} {target} = {value};")
                else:
                    lines.append(f"{space}{target} = {value};")

            # --- CHAMADAS DE HARDWARE ---
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Attribute): # servo.write()
                    lib = call.func.value.id
                    attr = call.func.attr
                    args = [self._get_value(a) for a in call.args]
                    if lib == "servo":
                        self.objects.add(f"Servo {args[0]};")
                        lines.append(f"{space}{args[0]}.{attr}({args[1] if len(args)>1 else ''});")
                elif isinstance(call.func, ast.Name): # delay()
                    name = call.func.id
                    args = [self._get_value(a) for a in call.args]
                    if name in self.HARDWARE_MAP:
                        lines.append(f"{space}{self.HARDWARE_MAP[name].format(*args)}")
        return lines

    def translate(self, py_code: str) -> str:
        try:
            tree = ast.parse(py_code)
            self.libraries, self.objects, self.globals, self.variables_declared = set(), set(), [], set()
            functions = []

            for node in tree.body:
                # 1. Bibliotecas
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if n.name == "servo": self.libraries.add("#include <Servo.h>")
                
                # 2. Variáveis Globais
                elif isinstance(node, ast.Assign):
                    target = node.targets[0].id
                    val = self._get_value(node.value)
                    tipo = "int" if val.replace("-","").isdigit() else "float"
                    self.variables_declared.add(target)
                    self.globals.append(f"{tipo} {target} = {val};")

                # 3. Funções (Setup / Loop)
                elif isinstance(node, ast.FunctionDef):
                    body = self._parse_body(node.body)
                    functions.append(f"void {node.name}() {{\n" + "\n".join(body) + "\n}")

            # Montagem Final Organizada por Zonas
            res = ["// --- WANDI ENGINE TRANSLATOR ---", ""]
            res.extend(list(self.libraries))
            res.extend(list(self.objects))
            res.append("")
            res.extend(self.globals)
            res.append("")
            res.extend(functions)
            
            return "\n".join(res)
        except Exception as e:
            return f"// ERRO CRÍTICO NO TRADUTOR: {e}"