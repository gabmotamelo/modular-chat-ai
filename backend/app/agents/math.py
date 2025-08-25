import re, time
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

SAFE = re.compile(r"[^0-9\+\-\*\/\^\(\)\.\sx]")

async def math_answer(message: str):
    t0 = time.perf_counter()
    expr = SAFE.sub("", message)
    try:
        ast = parse_expr(expr, transformations=(standard_transformations + (implicit_multiplication_application,)))
        val = float(ast.evalf())
        print(f"[MathAgent] expr='{expr}' -> {val}", flush=True)
        return (str(val), f"MathAgent evaluated in {int((time.perf_counter()-t0)*1000)}ms")
    except Exception:
        m = re.search(r"(\d+(?:\.\d+)?)\s*[x\*]\s*(\d+(?:\.\d+)?)", message, re.I)
        if m:
            v = float(m.group(1)) * float(m.group(2))
            print(f"[MathAgent] fallback '{message}' -> {v}", flush=True)
            return (str(v), f"MathAgent evaluated in {int((time.perf_counter()-t0)*1000)}ms")
        print(f"[MathAgent] fail '{message}'", flush=True)
        return ("Não consegui interpretar a expressão.", f"MathAgent failed in {int((time.perf_counter()-t0)*1000)}ms")
