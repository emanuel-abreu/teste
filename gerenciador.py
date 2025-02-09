import socket
import time
import json
from protocolo import HEADER
from atuador import Atuador
import os
import threading
from sensor import SensorCliente

CONFIG_FILE = "config.json"


class Gerenciador:
    def __init__(self, host="localhost", porta=8080):
        self.host = host
        self.porta = porta

        # Carregar a configuração do arquivo JSON
        configuracao = self.carregar_configuracao()
        self.temperatura_limite = configuracao.get("temperatura_limite", 25)
        self.sensores = configuracao.get("sensores", {})

        self.atuadores = {
            "refrigerador": Atuador(1, "refrigerador"),
            "luz_interna": Atuador(2, "luz_interna"),
            "alarme": Atuador(3, "alarme")
        }

        self.tempo_porta_aberta = None
        self.temporizador_alarme = None

    def carregar_configuracao(self):
        """Carrega a configuração (incluindo sensores) do arquivo JSON"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {}  # Retorna um dicionário vazio se o arquivo não existir

    def salvar_configuracao(self):
        """Salva a temperatura limite e os sensores no arquivo JSON"""
        configuracao = {
            "temperatura_limite": self.temperatura_limite,
            "sensores": self.sensores
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(configuracao, f)

    def iniciar_servidor(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.porta))
            s.listen()
            print(f"Servidor rodando em {self.host}:{self.porta}")

            while True:
                conn, addr = s.accept()
                with conn:
                    dados = conn.recv(1024)
                    if dados:
                        mensagem = json.loads(dados.decode())
                        resposta = self.processar_mensagem(mensagem)
                        conn.sendall(json.dumps(resposta).encode())

                self.controlar_atuadores()
                time.sleep(1)

    def processar_mensagem(self, mensagem):
        if mensagem.get("header") != HEADER:
            return {"status": "erro", "mensagem": "Protocolo inválido"}

        if mensagem["tipo"] == "sensor":
            sensor_tipo = mensagem["sensor_tipo"]
            valor = mensagem["valor"]

            if sensor_tipo in self.sensores:
                self.sensores[sensor_tipo] = valor
                print(f"Leitura recebida: {sensor_tipo} = {valor}")
                self.controlar_atuadores()
                return {"status": "ok", "mensagem": f"{sensor_tipo} = {valor}"}
            else:
                return {"status": "erro", "mensagem": "Sensor desconhecido"}

        elif mensagem["tipo"] == "consulta":
            sensor_tipo = mensagem["sensor_tipo"]

            if sensor_tipo == "temperatura":
                valor = self.temperatura_limite
                return {"status": "ok", "mensagem": f"Temperatura limite: {valor}°C"}

            valor = self.sensores.get(sensor_tipo, "Sem leitura disponível")
            return {"status": "ok", "mensagem": f"{sensor_tipo}: {valor}"}

        elif mensagem["tipo"] == "configuracao":
            if mensagem["parametro"] == "temperatura_limite":
                self.temperatura_limite = mensagem["valor"]
                self.salvar_configuracao()
                return {"status": "ok", "mensagem": f"Temperatura limite ajustada para {mensagem['valor']}°C"}

        return {"status": "erro", "mensagem": "Comando desconhecido"}

    def controlar_atuadores(self):
        temperatura = self.sensores.get(
            "temperatura", {}).get("limite_inferior", 0)
        if temperatura > self.temperatura_limite:
            self.atuadores["refrigerador"].alterar_estado("ligado")
        else:
            self.atuadores["refrigerador"].alterar_estado("desligado")

        if self.sensores.get("porta", "fechado") == "aberta":
            if self.tempo_porta_aberta is None:
                self.tempo_porta_aberta = time.time()
                self.iniciar_temporizador_alarme()
            self.atuadores["luz_interna"].alterar_estado("ligado")
        else:
            self.tempo_porta_aberta = None
            self.cancelar_temporizador_alarme()
            self.atuadores["luz_interna"].alterar_estado("desligado")

    def iniciar_temporizador_alarme(self):
        if self.temporizador_alarme:
            self.temporizador_alarme.cancel()
        self.temporizador_alarme = threading.Timer(30, self.ativar_alarme)
        self.temporizador_alarme.start()

    def cancelar_temporizador_alarme(self):
        if self.temporizador_alarme:
            self.temporizador_alarme.cancel()
            self.temporizador_alarme = None
        self.atuadores["alarme"].alterar_estado("desligado")

    def ativar_alarme(self):
        if self.sensores.get("porta", "fechado") == "aberta":
            self.atuadores["alarme"].alterar_estado("ligado")
            print("Alerta: Porta aberta por mais de 30 segundos!")


if __name__ == "__main__":
    gerenciador = Gerenciador()

    # Iniciar sensores em threads separadas
    for sensor_tipo in gerenciador.sensores.keys():
        threading.Thread(target=SensorCliente(
            sensor_tipo=sensor_tipo).rodar, daemon=True).start()

    gerenciador.iniciar_servidor()
