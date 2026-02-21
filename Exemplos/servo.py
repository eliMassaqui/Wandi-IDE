import servo  # Importa a biblioteca de controle de motores

# Variável para armazenar a posição (Sequência)
angulo = 0

def setup():
    # Configura o motor 'garra' no pino digital 9
    servo.attach(garra, 9)
    print("Braço Robótico Inicializado")

def loop():
    # 1. Abre a garra (Pilar da Sequência)
    angulo = 180
    servo.write(garra, angulo)
    delay(1000)
    
    # 2. Fecha a garra
    angulo = 0
    servo.write(garra, angulo)
    delay(1000)
    
    # 3. Verificação de segurança (Pilar da Decisão)
    if angulo == 0:
        print("Garra em posição de repouso")