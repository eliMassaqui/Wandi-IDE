def setup():
    Serial.begin(9600)
    pinMode(13, OUTPUT)

def loop():
    print("W")
    digitalWrite(13, HIGH)
    delay(1000)
    digitalWrite(13, LOW)
    delay(1000)