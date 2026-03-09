import servo

# Definição global para o compilador identificar o tipo de dado
angulo = 0

def setup():
    # Inicializa a comunicação e os pinos de saída
    Serial_begin(9600)
    pinMode(10, "OUTPUT")
    pinMode(9, "OUTPUT")
    
    # Configura o servo no pino digital 6
    servo.attach(6)
    println("Wandi IDE: Sistema Pronto")

def loop():
    global angulo

    # Move o servo para a posição atual
    servo.write(angulo)
    
    # Lê a posição confirmada no objeto servo
    posicao_atual = servo.read()
    
    # Feedback visual no Monitor Serial
    print("Angulo: ")
    println(posicao_atual) 

    # Acende os LEDs indicadores de movimento
    digitalWrite(10, "HIGH")
    digitalWrite(9, "HIGH")
    
    # Incrementa o passo (5 graus por ciclo)
    angulo = angulo + 5
    
    # Lógica de limite (0 a 180 graus)
    if angulo > 180:
        angulo = 0

    # Delay de estabilidade para a ponte WebSocket (100ms)
    delay(100) 

    # Apaga os LEDs após o movimento
    digitalWrite(10, "LOW")
    digitalWrite(9, "LOW")
    
    # Intervalo de repouso (100ms)
    delay(100)