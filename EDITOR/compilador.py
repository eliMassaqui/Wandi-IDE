import ast

class compiladorWandi:
    def __init__(self):
        self.libraries = set()
        self.objects = set()
        self.globals = []
        self.variables_declared = set()

        # Mapeamento de Comandos (Ajustado: Funções de retorno SEM ;)
        self.HARDWARE_MAP = {
            "pinMode": "pinMode({0}, {1});",
            "digitalWrite": "digitalWrite({0}, {1});",
            "digitalRead": "digitalRead({0})",    # Sem ; (Retorna valor)
            "analogRead": "analogRead({0})",      # Sem ; (Retorna valor)
            "analogWrite": "analogWrite({0}, {1});",
            "delay": "delay({0});",
            "print": "Serial.println({0});",
            "Serial_begin": "Serial.begin({0});"
        }

    def _get_value(self, node):
        """Converte nós Python em valores C++ com tratamento de erros"""
        if node is None:
            return "0"

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

        # SUPORTE A CHAMADAS (Ex: x = analogRead(0))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                name = node.func.id
                args = [self._get_value(a) for a in node.args]
                if name in self.HARDWARE_MAP:
                    # Retorna a função sem o ';' para uso em expressões
                    return self.HARDWARE_MAP[name].replace(";", "").format(*args)
            return "0"
            
        return "0" # Previne 'int valor = ;'

    def _parse_body(self, body, indent=2):
        """Processa blocos de código (Decisão e Iteração)"""
        lines = []
        space = " " * indent
        for node in body:
            # --- DECISÃO (if/else) ---
            if isinstance(node, ast.If):
                cond = self._get_value(node.test)
                lines.append(f"{space}if ({cond}) {{")
                lines.extend(self._parse_body(node.body, indent + 2))
                lines.append(f"{space}}}")
                if node.orelse:
                    lines.append(f"{space}else {{")
                    lines.extend(self._parse_body(node.orelse, indent + 2))
                    lines.append(f"{space}}}")

            # --- ITERAÇÃO (while) ---
            elif isinstance(node, ast.While):
                cond = self._get_value(node.test).replace("True", "true")
                lines.append(f"{space}while ({cond}) {{")
                lines.extend(self._parse_body(node.body, indent + 2))
                lines.append(f"{space}}}")

            # --- ATRIBUIÇÃO (valor = ...) ---
            elif isinstance(node, ast.Assign):
                target = node.targets[0].id
                value = self._get_value(node.value)
                
                if target not in self.variables_declared:
                    # Lógica lúcida para definir tipo
                    tipo = "float" if "." in value else "int"
                    self.variables_declared.add(target)
                    lines.append(f"{space}{tipo} {target} = {value};")
                else:
                    lines.append(f"{space}{target} = {value};")

            # --- CHAMADAS DE PROCEDIMENTO (Expr/Call) ---
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Attribute): # servo.write()
                    lib = call.func.value.id
                    attr = call.func.attr
                    args = [self._get_value(a) for a in call.args]
                    if lib == "servo":
                        self.objects.add(f"Servo {lib};") # Melhorado para nome do objeto
                        lines.append(f"{space}{lib}.{attr}({args[0] if args else ''});")
                
                elif isinstance(call.func, ast.Name): # delay(), digitalWrite()
                    name = call.func.id
                    args = [self._get_value(a) for a in call.args]
                    if name in self.HARDWARE_MAP:
                        # Aqui usamos o comando completo com ';'
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

            # Montagem Final Organizada
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