import socket
import time
import json
from protocolo import HEADER
from atuador import Atuador


class Gerenciador:
    def __init__(self, host="localhost", porta=8080):
        self.host = host
        self.porta = porta
        self.sensores = {}
        self.atuadores = {
            "refrigerador": Atuador(1, "refrigerador"),
            "luz_interna": Atuador(2, "luz_interna"),
            "alarme": Atuador(3, "alarme")
        }
        self.leituras = {}
        self.temperatura_limite = 5
        self.tempo_porta_aberta = None

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

                # Verifica se a porta está aberta por mais de 30 segundos
                self.verificar_porta_aberta()
                self.controlar_atuadores()
                time.sleep(1)  # Aguarda um pouco antes da próxima iteração

    def processar_mensagem(self, mensagem):
        if mensagem.get("header") != HEADER:
            return {"status": "erro", "mensagem": "Protocolo inválido"}

        if mensagem["tipo"] == "sensor":
            self.leituras[mensagem["sensor_tipo"]] = mensagem["valor"]
            print(
                f"Leitura recebida: {mensagem['sensor_tipo']} = {mensagem['valor']}")

            self.controlar_atuadores()
            return {"status": "ok", "mensagem": f"{mensagem['sensor_tipo']} = {mensagem['valor']}"}

        elif mensagem["tipo"] == "consulta":
            sensor_tipo = mensagem["sensor_tipo"]
            valor = self.leituras.get(sensor_tipo, "Sem leitura disponível")
            return {"status": "ok", "mensagem": f"{sensor_tipo}: {valor}"}

        elif mensagem["tipo"] == "configuracao":
            if mensagem["parametro"] == "temperatura_limite":
                self.temperatura_limite = mensagem["valor"]
                return {"status": "ok", "mensagem": f"Temperatura limite ajustada para {mensagem['valor']}°C"}

        return {"status": "erro", "mensagem": "Comando desconhecido"}

    def controlar_atuadores(self):
        if self.leituras.get("temperatura", 0) > self.temperatura_limite:
            self.atuadores["refrigerador"].alterar_estado("ligado")
        if self.leituras.get("porta") == "aberta":
            self.tempo_porta_aberta = time.time()
            self.atuadores["luz_interna"].alterar_estado("ligado")
        else:
            self.tempo_porta_aberta = None
            self.atuadores["luz_interna"].alterar_estado("desligado")

    def verificar_porta_aberta(self):
        if self.tempo_porta_aberta and (time.time() - self.tempo_porta_aberta) > 30:
            self.atuadores["alarme"].alterar_estado("ligado")


if __name__ == "__main__":
    gerenciador = Gerenciador()
    gerenciador.iniciar_servidor()
