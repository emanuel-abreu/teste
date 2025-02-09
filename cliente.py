import socket
import json
from protocolo import HEADER


class Cliente:
    def __init__(self, host="localhost", porta=5000, device_id=None):
        self.host = host
        self.porta = porta
        self.device_id = device_id

    def enviar_mensagem(self, mensagem):
        """Envia a mensagem ao servidor e aguarda a resposta."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.porta))
            s.sendall(json.dumps(mensagem).encode())

            resposta = s.recv(1024)  # Recebe resposta do servidor
            print("Servidor respondeu:", resposta.decode())  # Exibe resposta

    def consultar_leitura(self, sensor_tipo):
        """Consulta a última leitura do sensor desejado (temperatura, estoque ou porta)."""
        mensagem = {
            "header": HEADER,
            "tipo": "consulta",
            "sensor_tipo": sensor_tipo,
            "device_id": self.device_id  # Identificador do dispositivo
        }
        self.enviar_mensagem(mensagem)

    def consultar_estado_atuador(self, tipo_atuador):
        """Consulta o estado do atuador especificado (refrigerador, luz interna ou alarme)."""
        mensagem = {
            "header": HEADER,
            "tipo": "consulta",
            "sensor_tipo": tipo_atuador,
            "device_id": self.device_id
        }
        self.enviar_mensagem(mensagem)

    def configurar_temperatura(self, nova_temperatura):
        """Configura o limite de temperatura da geladeira."""
        mensagem = {
            "header": HEADER,
            "tipo": "configuracao",
            "parametro": "temperatura_limite",
            "valor": nova_temperatura,
            "device_id": self.device_id
        }
        self.enviar_mensagem(mensagem)


if __name__ == "__main__":
    device_id = input("Informe o ID do seu dispositivo: ")
    cliente = Cliente(device_id=device_id)

    while True:
        print("\n1 - Consultar leitura do sensor")
        print("2 - Consultar estado do atuador")
        print("3 - Configurar temperatura ideal")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            sensor = input(
                "Digite o tipo do sensor (temperatura, estoque, porta): ")
            cliente.consultar_leitura(sensor)
        elif opcao == "2":
            atuador = input(
                "Digite o tipo de atuador (refrigerador, luz, alarme): ")
            cliente.consultar_estado_atuador(atuador)
        elif opcao == "3":
            temp = int(input("Digite a nova temperatura ideal: "))
            cliente.configurar_temperatura(temp)
        else:
            print("Opção inválida.")
