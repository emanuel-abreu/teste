import socket
import json
import random
import time
import os
from protocolo import HEADER

CONFIG_FILE = "config.json"


class SensorCliente:
    def __init__(self, host="localhost", porta=8080, sensor_tipo="temperatura"):
        self.host = host
        self.porta = porta
        self.sensor_tipo = sensor_tipo
        self.leituras = {}  # Armazena leituras, incluindo temperatura limite
        self.config = self.carregar_configuracao()  # Carrega as configurações
        # A temperatura inicial vem do config
        self.temperatura_atual = self.config['sensores']['temperatura_atual']
        # Limite da temperatura
        self.temperatura_limite = self.config['temperatura_limite']
        self.estado_refrigerador = "desligado"  # Estado inicial do refrigerador

    def carregar_configuracao(self):
        """Carrega a configuração do arquivo JSON."""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print("Erro ao carregar config.json.")
        return {}

    def gerar_leitura(self):
        """Gera leitura baseada no tipo de sensor."""
        if self.sensor_tipo == "temperatura":
            if self.temperatura_atual > self.temperatura_limite:
                # Simula resfriamento gradual
                self.temperatura_atual -= random.uniform(0.5, 1.5)
                self.estado_refrigerador = "ligado"  # Liga o refrigerador
            elif self.temperatura_atual < self.temperatura_limite:
                # Simula aquecimento
                self.temperatura_atual += random.uniform(0.5, 1.5)
                self.estado_refrigerador = "desligado"  # Desliga o refrigerador

            return round(self.temperatura_atual, 1)

        elif self.sensor_tipo == "estoque":
            # Retorna o valor do estoque diretamente
            return self.config['sensores']['estoque']

        elif self.sensor_tipo == "porta":
            # Retorna o status da porta
            return self.config['sensores']['porta']

    def enviar_leitura(self):
        """Envia a leitura para o servidor."""
        leitura = self.gerar_leitura()
        mensagem = {
            "header": HEADER,
            "tipo": "sensor",
            "sensor_tipo": self.sensor_tipo,
            "valor": leitura,
            "estado_refrigerador": self.estado_refrigerador,  # Inclui o estado do refrigerador
            "temperatura_atual": self.temperatura_atual,  # Inclui a temperatura atual
        }

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.porta))
            s.sendall(json.dumps(mensagem).encode())
            resposta = s.recv(1024)
            print(f"Servidor respondeu: {resposta.decode()}")

    def rodar(self):
        while True:
            self.enviar_leitura()
            time.sleep(5)  # Aguarda 5 segundos antes da próxima leitura
