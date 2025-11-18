import os
import requests
from sqlalchemy.orm import Session

from app.models import (
    User,
    ScoreSession,
    ScoreAnswer,
    ScorePillars,
)
from app.services.pdf_creator import gerar_pdf_relatorio

from app.services.gpt_logic import (
    montar_interpretacao_combinada,
    montar_convite_sessao,
)

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
API_URL = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v20.0")


# ------------------------------------------------------------
#   ENVIAR MENSAGEM NO WHATSAPP (TEXTO)
# ------------------------------------------------------------
def enviar_whatsapp_texto(to, texto):
    url = f"{API_URL}/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": texto},
    }
    requests.post(url, json=payload, headers=headers)


# ------------------------------------------------------------
#   ENVIAR PDF NO WHATSAPP
# ------------------------------------------------------------
def enviar_whatsapp_documento(to, pdf_path, nome_arquivo="relatorio.pdf"):
    url = f"{API_URL}/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    }

    with open(pdf_path, "rb") as f:
        files = {
            "document": (nome_arquivo, f, "application/pdf")
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document"
        }
        requests.post(
            url,
            data=data,
            files=files,
            headers=headers
        )


# ------------------------------------------------------------
#   MAPA DE PILARES E PERGUNTAS
# ------------------------------------------------------------
PILAR_MAP = {
    1:"tempo",2:"tempo",3:"tempo",
    4:"familia",5:"familia",6:"familia",
    7:"decisao",8:"decisao",9:"decisao",
    10:"dinheiro",11:"dinheiro",12:"dinheiro",
    13:"fe_principios",14:"fe_principios",15:"fe_principios",
    16:"legado",17:"legado",18:"legado",
    19:"energia_saude",20:"energia_saude",21:"energia_saude",
    22:"networking",23:"networking",24:"networking",
    25:"aprendizado",26:"aprendizado",27:"aprendizado",
    28:"risco_medo",29:"risco_medo",30:"risco_medo",
}

QUESTION_TEXT = {
    1: "Minha agenda reflete claramente o que será importante para mim nos próximos 10 anos.",
    2: "Consigo dizer “não” para oportunidades que não mudam meu futuro.",
    3: "Tenho blocos consistentes de tempo para pensar e decidir.",
    4: "Tenho rituais semanais de presença real com minha família.",
    5: "Meus filhos (ou futuros filhos) aprendem comigo sobre valores e decisões.",
    6: "Meu cônjuge está integrado ao meu mundo e decisões.",
    7: "Foco em no máximo 3 grandes frentes pelos próximos anos.",
    8: "Tenho coragem de encerrar projetos que drenam energia.",
    9: "Minhas decisões seguem critérios simples e não-negociáveis.",
    10: "Invisto lucros em pessoas e projetos que multiplicam sem mim.",
    11: "Dinheiro nunca fica parado — circula de forma estratégica.",
    12: "Tenho sistemas que multiplicam dinheiro mesmo sem eu trabalhar.",
    13: "Minhas decisões refletem meus princípios, mesmo quando custam dinheiro.",
    14: "Tenho propósito claro que guia minha rotina.",
    15: "Sou o mesmo no trabalho, na família e comigo mesmo.",
    16: "Discuto abertamente sobre dinheiro e princípios com minha família.",
    17: "Transmito sabedoria, não apenas recursos.",
    18: "Preparo sucessores para multiplicar, não apenas manter.",
    19: "Durmo o suficiente para clareza e presença.",
    20: "Tenho uma rotina mínima de movimento físico.",
    21: "Faço escolhas alimentares com intenção.",
    22: "Tenho uma rede pequena, mas profunda, de confiança.",
    23: "Invisto tempo em alianças estratégicas.",
    24: "Gero valor antes de pedir.",
    25: "Aplico imediatamente o que aprendo.",
    26: "Não começo algo novo antes de implementar o que já aprendi.",
    27: "Consumo informação com estratégia.",
    28: "Decido mesmo sentindo medo.",
    29: "Penso no longo prazo mesmo em crises.",
    30: "Avalio riscos com método, não com paralisia.",
}


# ------------------------------------------------------------
#   UTILITÁRIOS
# ------------------------------------------------------------
def extract_message_and_number(body):
    number = body.get("from")
    message = (body.get("text") or "").strip()
    return number, message


def get_or_create_user(db: Session, whatsapp_number: str):
    user = db.query(User).filter_by(whatsapp_number=whatsapp_number).first()
    if user:
        return user
    user = User(whatsapp_number=whatsapp_number)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_session(db: Session, user: User):
    session = db.query(ScoreSession).filter_by(
        user_id=user.id,
        status="em_andamento"
    ).first()
    if session:
        return session
    session = ScoreSession(
        user_id=user.id,
        estado_atual="COLETAR_NOME"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def pergunta_score(n):
    return (
        f"Pergunta {n}/30:\n\n"
        "Responda de 1 a 5:\n"
        "1 = Nunca\n5 = Sempre\n\n"
        f"{QUESTION_TEXT[n]}"
    )


# ------------------------------------------------------------
#   CÁLCULO DOS PILARES
# ------------------------------------------------------------
def calcular_pilares(db, session):
    respostas = session.answers
    soma = {
        "tempo":0,"familia":0,"decisao":0,"dinheiro":0,
        "fe_principios":0,"legado":0,"energia_saude":0,
        "networking":0,"aprendizado":0,"risco_medo":0,
    }
    for r in respostas:
        soma[r.pillar_code] += r.answer_value

    db.add(ScorePillars(score_session_id=session.id, **soma))
    db.commit()
    return soma


def determinar_pilares(soma):
    return max(soma, key=soma.get), min(soma, key=soma.get)


def calcular_score_total(soma):
    return sum(soma.values())


def determinar_perfil(score):
    if score >= 120:
        return "Realizador Visionário"
    if score >= 100:
        return "Construtor Consistente"
    if score >= 80:
        return "Operador em Evolução"
    return "Sobrecarregado em Recuperação"


# ------------------------------------------------------------
#   FINALIZAÇÃO DO SCORE / PDF / IA / WHATSAPP
# ------------------------------------------------------------
def finalizar_score(db, user, session, number):
    soma = calcular_pilares(db, session)
    pilar_forte, pilar_toxico = determinar_pilares(soma)
    score = calcular_score_total(soma)
    perfil = determinar_perfil(score)

    session.pilar_dominante = pilar_forte
    session.pilar_toxico = pilar_toxico
    session.score_total = score
    session.perfil_nome = perfil
    session.status = "concluida"
    db.commit()

    # IA cria as interpretações
    interpretacao = montar_interpretacao_combinada(perfil, pilar_forte, pilar_toxico)
    convite = montar_convite_sessao(perfil, pilar_toxico)

    dados_pdf = {
        "nome": user.nome,
        "score_total": score,
        "perfil": perfil,
        "pilar_dominante": pilar_forte,
        "pilar_toxico": pilar_toxico,
        "pilares": soma,
        "interpretacao": interpretacao,
        "convite_sessao": convite,
        "renda_qualificada": session.renda_qualificada,
    }

    pdf_path = gerar_pdf_relatorio(dados_pdf, session.id)
    session.pdf_url = pdf_path
    db.commit()

    # envia PDF
    enviar_whatsapp_texto(number, "Seu Score de Riqueza está pronto. Estou enviando seu relatório…")
    enviar_whatsapp_documento(number, pdf_path)

    if session.renda_qualificada:
        enviar_whatsapp_texto(
            number,
            "📌 *Recomendação Final*\n\n"
            "Existe um ponto sensível drenando força e clareza do seu ciclo atual. "
            "Podemos corrigir isso de forma objetiva em uma Sessão Solucionista™.\n\n"
            "Quer ver opções de agenda?"
        )
    else:
        enviar_whatsapp_texto(
            number,
            "Seu relatório está pronto! Aplique as recomendações para fortalecer seus próximos passos."
        )


# ------------------------------------------------------------
#   MÁQUINA DE ESTADOS DO WHATSAPP
# ------------------------------------------------------------
def process_message(db: Session, user: User, session: ScoreSession, msg: str, number: str):

    # COLETAR NOME
    if session.estado_atual == "COLETAR_NOME":
        session.estado_atual = "AGUARDANDO_NOME"
        db.commit()
        return enviar_whatsapp_texto(number, "Vamos começar. Qual é o seu nome completo?")

    if session.estado_atual == "AGUARDANDO_NOME":
        user.nome = msg
        session.estado_atual = "COLETAR_INSTAGRAM"
        db.commit()
        return enviar_whatsapp_texto(number, f"Certo, {user.nome}. Qual é o seu @ do Instagram?")

    # INSTAGRAM
    if session.estado_atual == "COLETAR_INSTAGRAM":
        user.instagram = msg
        session.estado_atual = "COLETAR_RENDA"
        db.commit()
        return enviar_whatsapp_texto(number,
            "Agora me diga sua renda mensal:\n\n"
            "1. Até R$ 5.000\n"
            "2. R$ 5.001–10.000\n"
            "3. R$ 10.001–20.000\n"
            "4. R$ 20.001–50.000\n"
            "5. R$ 50.001–100.000\n"
            "6. Acima de R$ 100.000\n\n"
            "Responda apenas com o número."
        )

    # RENDA
    if session.estado_atual == "COLETAR_RENDA":
        if msg not in ["1","2","3","4","5","6"]:
            return enviar_whatsapp_texto(number, "Responda com um número de 1 a 6.")

        renda_map = {
            "1":"Até R$ 5.000",
            "2":"R$ 5.001–10.000",
            "3":"R$ 10.001–20.000",
            "4":"R$ 20.001–50.000",
            "5":"R$ 50.001–100.000",
            "6":"Acima de R$ 100.000",
        }

        user.renda_faixa = renda_map[msg]
        session.renda_qualificada = msg != "1"
        session.estado_atual = "PERGUNTA_1"
        db.commit()

        return enviar_whatsapp_texto(number,
            "Vamos iniciar as 30 perguntas do Score de Riqueza.\n"
            "Responda sempre com números de 1 a 5.\n\n"
            + pergunta_score(1)
        )

    # PERGUNTAS 1 A 30
    if session.estado_atual.startswith("PERGUNTA_"):
        n = int(session.estado_atual.split("_")[1])

        if msg not in ["1","2","3","4","5"]:
            return enviar_whatsapp_texto(number, "Responda com um número de 1 a 5.")

        resposta = ScoreAnswer(
            score_session_id=session.id,
            question_number=n,
            pillar_code=PILAR_MAP[n],
            answer_value=int(msg),
        )
        db.add(resposta)
        db.commit()

        if n == 30:
            finalizar_score(db, user, session, number)
            return

        session.estado_atual = f"PERGUNTA_{n+1}"
        db.commit()
        return enviar_whatsapp_texto(number, pergunta_score(n+1))

    # fallback
    enviar_whatsapp_texto(number, "Vamos seguir passo a passo.")