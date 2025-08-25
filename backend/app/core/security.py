import bleach

SUSPICIOUS = ("ignore previous", "system prompt", "developer instructions",
              "jailbreak", "reveal", "act as", "do anything")

def sanitize(text: str) -> str:
    return bleach.clean(text, tags=[], attributes={}, strip=True)

def looks_malicious(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in SUSPICIOUS)
