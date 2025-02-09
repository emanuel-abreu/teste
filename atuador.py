import json
from protocolo import HEADER


class Atuador:
    def __init__(self, atuador_id, tipo):
        self.atuador_id = atuador_id
        self.tipo = tipo
        self.estado = "desligado"

    def alterar_estado(self, novo_estado):
        if novo_estado not in ["ligado", "desligado"]:
            print(
                f"Estado inválido: {novo_estado}. O atuador pode ser 'ligado' ou 'desligado'.")
            return False

        if self.estado == novo_estado:
            print(f"{self.tipo} já está {novo_estado}. Nenhuma alteração necessária.")
            return False

        self.estado = novo_estado
        print(f"{self.tipo} foi {novo_estado}")
        return True

    def criar_mensagem(self):
        return json.dumps({
            "header": HEADER,
            "tipo": "atuador",
            "atuador_id": self.atuador_id,
            "tipo_atuador": self.tipo,
            "estado": self.estado
        })
