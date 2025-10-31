#!/usr/bin/env python3
"""
Visual Python Parser
--------------------
Parses natural English-like Python syntax and executes or outputs valid Python code.
"""

import re

def parse_visual_python(code: str) -> str:
    """Convert Visual Python pseudo-code into executable Python."""
    lines = code.strip().split("\n")
    output = []
    indent = 0

    def add_line(py_line):
        output.append("    " * indent + py_line)

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        # --- Variable creation ---
        if line.lower().startswith("create variable"):
            # Example: Create variable x = 10
            m = re.match(r"create variable (\w+)\s*=\s*(.*)", line, re.I)
            if m:
                name, value = m.groups()
                add_line(f"{name} = {value}")
                continue

        # --- Print command ---
        if line.lower().startswith("print "):
            text = line[6:].strip()
            add_line(f"print({text})")
            continue

        # --- If statements ---
        if line.lower().startswith("if "):
            expr = line[3:].strip()
            expr = expr.replace(" is greater than ", " > ")
            expr = expr.replace(" is less than ", " < ")
            expr = expr.replace(" is equal to ", " == ")
            expr = expr.replace(" is not equal to ", " != ")
            expr = expr.replace(" then", "")
            add_line(f"if {expr}:")
            indent += 1
            continue

        # --- End block ---
        if line.lower() == "end":
            indent = max(0, indent - 1)
            continue

        # --- Else block ---
        if line.lower().startswith("else"):
            indent = max(0, indent - 1)
            add_line("else:")
            indent += 1
            continue

        # --- For loops ---
        if line.lower().startswith("for each"):
            # Example: For each item in items
            m = re.match(r"for each (\w+) in (.+)", line, re.I)
            if m:
                var, seq = m.groups()
                add_line(f"for {var} in {seq}:")
                indent += 1
                continue

        # --- While loops ---
        if line.lower().startswith("while "):
            expr = line[6:].strip()
            expr = expr.replace(" is greater than ", " > ")
            expr = expr.replace(" is less than ", " < ")
            expr = expr.replace(" is equal to ", " == ")
            add_line(f"while {expr}:")
            indent += 1
            continue

        # --- Default: raw Python fallback ---
        add_line(line)

    return "\n".join(output)


# Demo usage
if __name__ == "__main__":
    print("Enter Visual Python code (end with blank line):\n")
    buf = []
    while True:
        line = input("> ")
        if not line.strip():
            break
        buf.append(line)

    vp_code = "\n".join(buf)
    py_code = parse_visual_python(vp_code)
    print("\n🧠 Translated Python:\n")
    print(py_code)

    print("\n⚙️ Executing:\n")
    exec(py_code)
