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
        self.device_id = random.randint(1000, 9999)  # ID único do sensor
        self.leituras = {}
        self.config = self.carregar_configuracao()
        self.temperatura_atual = self.config['sensores']['temperatura_atual']
        self.temperatura_limite = self.config['temperatura_limite']
        self.estoque_atual = self.config['sensores']['estoque']
        self.capacidade_maxima = self.config['sensores'].get(
            'capacidade_maxima', 100)  # capacidade máxima da geladeira
        self.estado_refrigerador = "desligado"

    def carregar_configuracao(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print("Erro ao carregar config.json.")
        return {}

    def conectar_ao_servidor(self):
        """Estabelece conexão inicial com o servidor e recebe confirmação."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.porta))
            handshake_msg = {
                "header": HEADER,
                "tipo": "handshake",
                "sensor_tipo": self.sensor_tipo,
                "device_id": self.device_id
            }
            s.sendall(json.dumps(handshake_msg).encode())
            resposta = s.recv(1024).decode()
            resposta_json = json.loads(resposta)

            if resposta_json.get("status") == "ok":
                print(
                    f"Sensor {self.device_id} ({self.sensor_tipo}) conectado com sucesso.")
                return True
            else:
                print(
                    f"Erro ao conectar sensor {self.device_id}: {resposta_json.get('mensagem')}")
                return False

    def gerar_leitura(self):
        if self.sensor_tipo == "temperatura":
            if self.temperatura_atual > self.temperatura_limite:
                self.temperatura_atual -= random.uniform(0.5, 1.5)
                self.estado_refrigerador = "ligado"
            elif self.temperatura_atual < self.temperatura_limite:
                self.temperatura_atual += random.uniform(0.5, 1.5)
                self.estado_refrigerador = "desligado"
            return round(self.temperatura_atual, 1)
        elif self.sensor_tipo == "estoque":
            percentual_estoque = (self.estoque_atual /
                                  self.capacidade_maxima) * 100
            return round(percentual_estoque, 1)
        elif self.sensor_tipo == "porta":
            return self.config['sensores']['porta']

    def enviar_leitura(self):
        leitura = self.gerar_leitura()
        mensagem = {
            "header": HEADER,
            "tipo": "sensor",
            "sensor_tipo": self.sensor_tipo,
            "device_id": self.device_id,
            "valor": leitura
        }
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.porta))
            s.sendall(json.dumps(mensagem).encode())
            resposta = s.recv(1024)
            print(f"Servidor respondeu: {resposta.decode()}")

    def rodar(self):
        if not self.conectar_ao_servidor():
            return
        while True:
            self.enviar_leitura()
            time.sleep(10)
