import servo

angulo = 0

def setup():
    Serial_begin(9600)
    pinMode(10, OUTPUT)
    pinMode(9, OUTPUT)
    servo.attach(6)

def loop():
    global angulo

    print("W")

    digitalWrite(10, HIGH)
    digitalWrite(9, HIGH)

    servo.write(angulo)
    angulo = angulo + 5

    if angulo > 180:
        angulo = 0

    delay(50)

    digitalWrite(10, LOW)
    digitalWrite(9, LOW)
    delay(200)