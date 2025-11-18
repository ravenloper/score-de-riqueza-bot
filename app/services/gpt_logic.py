import os
from openai import OpenAI


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Isso ajuda a diagnosticar rápido se tiver algo errado com o .env
        raise RuntimeError("OPENAI_API_KEY não encontrada no ambiente. Verifique seu arquivo .env.")
    return OpenAI(api_key=api_key)


def get_model():
    return os.getenv("OPENAI_MODEL", "gpt-5.1-mini")


# ------------------------------------------------------------
#   Monta interpretação combinando perfil + pilar forte + pilar tóxico
# ------------------------------------------------------------
def montar_interpretacao_combinada(perfil, pilar_forte, pilar_toxico):
    client = get_client()
    model = get_model()

    prompt = f"""
Você é um especialista em desempenho humano, liderança, psicologia aplicada e leitura estratégica.
Combine estes elementos em uma interpretação precisa, profunda e elegante:

Perfil: {perfil}
Pilar forte: {pilar_forte}
Pilar tóxico: {pilar_toxico}

Crie um texto:
- direto
- emocionalmente inteligente
- com alta precisão psicológica
- que mostre força, risco e direção
- sem clichês
- com densidade e autoridade

O texto deve ter entre 6 e 10 linhas.

Comece falando do perfil.
Depois conecte o pilar forte.
Finalize com a leitura crítica do pilar tóxico.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Você é Fernando Tessaro, versão maximizada pela IA, especialista em Solucionismo e riqueza integral."
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


# ------------------------------------------------------------
#   Convite para Sessão Solucionista baseado no pilar tóxico
# ------------------------------------------------------------
def montar_convite_sessao(perfil, pilar_toxico):
    client = get_client()
    model = get_model()

    prompt = f"""
Crie um convite curto e poderoso para uma Sessão Solucionista™ baseado no pilar tóxico.

Perfil: {perfil}
Pilar tóxico: {pilar_toxico}

O convite deve:
- ser direto
- forte
- com autoridade e precisão
- mostrar que há uma solução objetiva
- manter linguagem premium
- máximo de 4 linhas
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Você é Fernando Tessaro, especialista em Solucionismo, falando com um empresário de alta renda."
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )

    return response.choices[0].message.content.strip()