import datetime

def _detectar_intencao_reclamacao(mensagem):
    m = mensagem.lower()
    return any(p in m for p in [
        "gerar reclamacao","gerar reclamação","texto reclamacao","texto de reclamacao",
        "escrever reclamacao","redigir reclamacao","reclamacao formal","texto formal",
        "modelo reclamacao","carta reclamacao","reclamar formalmente","quero reclamar",
        "me ajuda a reclamar","como reclamar por escrito",
    ])

