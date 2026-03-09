import servo

pos = 0

def setup():
    Serial_begin(9600) 
    servo.attach(6)
    println("Sistema Iniciado - Varredura 0-180")

def loop():
    # Movimento de ida: 0 a 180 graus
    for pos in range(0, 180, 1):
        servo.write(pos)
        
        if pos % 20 == 0:
            print("Indo: ")
            println(pos)
            
        delay(15)

    # Movimento de volta: 180 a 0 graus
    for pos in range(180, 0, -1):
        servo.write(pos)
        
        if pos % 20 == 0:
            print("Voltando: ")
            println(pos)
            
        delay(15)