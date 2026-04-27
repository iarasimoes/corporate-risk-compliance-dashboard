import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


def ask_ollama(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        return response.json().get("response", "")

    except Exception as e:
        return f"Error: {str(e)}"


def summarize_news(title):
    prompt = f"""
    Summarize this news in 1 short sentence:

    {title}
    """

    return ask_ollama(prompt)


def explain_risk(title):
    prompt = f"""
    Explain why this news could represent a corporate risk:

    {title}
    """

    return ask_ollama(prompt)
