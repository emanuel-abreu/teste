import socket
import json
import random
import time
from protocolo import HEADER


class SensorCliente:
    def __init__(self, host="localhost", porta=8080, sensor_tipo="temperatura"):
        self.host = host
        self.porta = porta
        self.sensor_tipo = sensor_tipo
        self.leituras = {}  # Armazena leituras, incluindo temperatura limite
        self.temperatura_atual = 10  # Inicializa temperatura com um valor aleatório

    def gerar_leitura(self):
        if self.sensor_tipo == "temperatura":
            limite = self.leituras.get("temperatura_limite", self.temperatura_atual)  # Se não houver limite, mantém a temperatura atual
            if self.temperatura_atual > limite:
                self.temperatura_atual -= 1  # Simula resfriamento gradual
            return self.temperatura_atual
        elif self.sensor_tipo == "estoque":
            return random.randint(10, 100)
        elif self.sensor_tipo == "porta":
            return "aberta"

    def consultar_temperatura_limite(self):
        """Consulta a temperatura limite armazenada no servidor"""
        mensagem = {
            "header": HEADER,
            "tipo": "consulta",
            "sensor_tipo": "temperatura_limite"
        }

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.porta))
            s.sendall(json.dumps(mensagem).encode())

            resposta_bruta = s.recv(1024).decode()
            if not resposta_bruta:
                print("Erro: Servidor não enviou resposta.")
                return  # Evita tentar processar JSON vazio

            try:
                resposta = json.loads(resposta_bruta)
            except json.JSONDecodeError:
                print(f"Erro: Resposta inválida do servidor: {resposta_bruta}")
                return  # Evita exceções ao tentar acessar chaves inválidas

            if resposta.get("status") == "ok":
                try:
                    self.leituras["temperatura_limite"] = float(resposta["mensagem"])
                    print(f"Temperatura limite recebida: {self.leituras['temperatura_limite']}°C")
                except ValueError:
                    print(f"Erro: Temperatura limite inválida recebida ({resposta['mensagem']}). Mantendo valor anterior.")
                    self.leituras["temperatura_limite"] = self.temperatura_atual  # Evita erros na comparação


    def enviar_leitura(self):
        """Antes de enviar a leitura, consulta a temperatura limite"""
        self.consultar_temperatura_limite()

        mensagem = {
            "header": HEADER,
            "tipo": "sensor",
            "sensor_tipo": self.sensor_tipo,
            "valor": self.gerar_leitura()
        }

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.porta))
            s.sendall(json.dumps(mensagem).encode())
            resposta = s.recv(1024)
            print(f"Servidor respondeu: {resposta.decode()}")

    def rodar(self):
        """Envia leituras periodicamente"""
        while True:
            self.enviar_leitura()
            time.sleep(5)  # Envia a cada 5 segundos


if __name__ == "__main__":
    sensor_tipo = input("Escolha o tipo de sensor (temperatura, estoque, porta): ")
    sensor = SensorCliente(sensor_tipo=sensor_tipo)
    sensor.rodar()
