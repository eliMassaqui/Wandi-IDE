import ast

class compiladorWandi:
    def __init__(self):
        self.libraries = set()
        self.objects = set()
        self.globals = []
        self.variables_declared = set()

        self.HARDWARE_MAP = {
            "pinMode": "pinMode({0}, {1});",
            "digitalWrite": "digitalWrite({0}, {1});",
            "delay": "delay({0});",
            "print": "Serial.print({0});",
            "println": "Serial.println({0});",
            "Serial_begin": "Serial.begin({0});"
        }

    def _get_value(self, node):
        if node is None: return "0"
        if isinstance(node, ast.Constant):
            return f'"{node.value}"' if isinstance(node.value, str) else str(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return f"-{self._get_value(node.operand)}"
        elif isinstance(node, ast.BinOp):
            left = self._get_value(node.left)
            right = self._get_value(node.right)
            ops = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Mod: "%"}
            return f"{left} {ops[type(node.op)]} {right}"
        elif isinstance(node, ast.Compare):
            left = self._get_value(node.left)
            op = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", 
                  ast.Gt: ">", ast.GtE: ">="}[type(node.ops[0])]
            right = self._get_value(node.comparators[0])
            return f"{left} {op} {right}"
        return "0"

    def _parse_body(self, body, indent=2):
        lines = []
        space = " " * indent
        for node in body:
            # --- ESTRUTURAS DE CONTROLE (IF) ---
            if isinstance(node, ast.If):
                cond = self._get_value(node.test)
                lines.append(f"{space}if ({cond}) {{")
                lines.extend(self._parse_body(node.body, indent + 2))
                lines.append(f"{space}}}")

            # --- FOR LOOPS (RANGE) ---
            elif isinstance(node, ast.For):
                target = node.target.id
                if isinstance(node.iter, ast.Call) and node.iter.func.id == "range":
                    args = node.iter.args
                    start = self._get_value(args[0])
                    stop_raw = self._get_value(args[1])
                    step = self._get_value(args[2]) if len(args) > 2 else "1"

                    if "-" in step: # Lógica para contagem regressiva
                        op = ">="
                        lines.append(f"{space}for (int {target} = {start}; {target} {op} {stop_raw}; {target} -= {step.lstrip('-')}) {{")
                    else: # Lógica para contagem progressiva
                        op = "<="
                        # Ajuste para incluir o último número (comportamento comum em Arduino loops)
                        lines.append(f"{space}for (int {target} = {start}; {target} {op} {stop_raw}; {target} += {step}) {{")
                    
                    lines.extend(self._parse_body(node.body, indent + 2))
                    lines.append(f"{space}}}")

            # --- ATRIBUIÇÃO ---
            elif isinstance(node, ast.Assign):
                target = node.targets[0].id
                val = self._get_value(node.value)
                if target not in self.variables_declared:
                    self.variables_declared.add(target)
                    lines.append(f"{space}int {target} = {val};")
                else:
                    lines.append(f"{space}{target} = {val};")

            # --- CHAMADAS DE FUNÇÃO E MÉTODOS ---
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                args = [self._get_value(a) for a in call.args]
                
                # Trata servo.write ou myServo.write
                if isinstance(call.func, ast.Attribute):
                    obj = call.func.value.id
                    metodo = call.func.attr
                    if obj in ["servo", "myServo"]:
                        self.libraries.add("#include <Servo.h>")
                        self.objects.add("Servo myServo;")
                        obj = "myServo" # Normaliza para myServo no C++
                    lines.append(f"{space}{obj}.{metodo}({', '.join(args)});")
                
                elif isinstance(call.func, ast.Name) and call.func.id in self.HARDWARE_MAP:
                    lines.append(f"{space}{self.HARDWARE_MAP[call.func.id].format(*args)}")
        return lines

    def translate(self, py_code: str) -> str:
        tree = ast.parse(py_code)
        self.libraries, self.objects, self.globals, self.variables_declared = set(), set(), [], set()
        functions = []

        for node in tree.body:
            # Ignora o 'import servo' mas sabe que deve usar a lib se ele existir
            if isinstance(node, ast.Import) and node.names[0].name == "servo":
                self.libraries.add("#include <Servo.h>")
                self.objects.add("Servo myServo;")
            
            elif isinstance(node, ast.Assign):
                target = node.targets[0].id
                val = self._get_value(node.value)
                self.variables_declared.add(target)
                self.globals.append(f"int {target} = {val};")
            
            elif isinstance(node, ast.FunctionDef):
                body = self._parse_body(node.body)
                functions.append(f"void {node.name}() {{\n" + "\n".join(body) + "\n}")
        
        res = ["// --- WANDI ENGINE: LOGICA DO ARDUINO ---", ""]
        res.extend(sorted(list(self.libraries)))
        res.extend(sorted(list(self.objects)))
        res.append("")
        res.extend(self.globals)
        res.append("")
        res.extend(functions)
        return "\n".join(res)