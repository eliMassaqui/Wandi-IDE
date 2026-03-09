import servo

angulo = 0
passo = 1      
intervalo = 15 

def setup():
    # Baud rate de 9600 é lento; se possível, use 115200 no futuro
    Serial_begin(9600)
    servo.attach(6)
    println("Servo Iniciado")

def loop():
    global angulo

    # Envia a posição para o servo
    servo.write(angulo)
    
    # ESTRATÉGIA LÚCIDA: 
    # Só imprime se o ângulo for múltiplo de 20. 
    # Isso evita o flood de dados (os "muitos zeros" ou repetições inúteis).
    if angulo % 20 == 0:
        print("Angulo Atual: ")
        println(angulo) 

    # Lógica de incremento
    angulo = angulo + passo
    
    # Reset: volta ao zero quando atinge o limite
    if angulo > 180:
        angulo = 0

    delay(intervalo)