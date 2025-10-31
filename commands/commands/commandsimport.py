import os
import ast
import operator as op
import sys 
import re
import inspect

def register_command(name):
    """Temporary decorator for plugin compatibility."""
    from __main__ import registered_commands
    def wrapper(func):
        registered_commands[name] = func
        return func
    return wrapper

@register_command("cal")
def cal_cmd(args):
    """Evaluate a basic algebra expression using BEDMAS order."""
    if not args:
        print("Usage: cal <expression>")
        print("Example: cal (3 + 4) * 2^3 / 4")
        return

    expression = " ".join(args)

    # Allowed operators (safe evaluation)
    operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.Mod: op.mod,
        ast.USub: op.neg,
    }

    def eval_expr(node):
        """Recursively evaluate an AST node."""
        if isinstance(node, ast.Num):  # numbers
            return node.n
        elif isinstance(node, ast.BinOp):  # binary operation
            left = eval_expr(node.left)
            right = eval_expr(node.right)
            return operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):  # negative numbers
            return operators[type(node.op)](eval_expr(node.operand))
        else:
            raise TypeError(f"Unsupported expression: {node}")

    try:
        # Replace ^ with ** for exponentiation
        expression = expression.replace("^", "**")

        # Parse safely
        node = ast.parse(expression, mode="eval").body
        result = eval_expr(node)
        print(f"🧮 {expression.replace('**', '^')} = {result}")
    except ZeroDivisionError:
        print("❌ Error: Division by zero.")
    except Exception as e:
        print(f"⚠️ Invalid expression: {e}")
        
