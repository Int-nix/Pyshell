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
        
@register_command("goto")
def goto_cmd(args):
    """
    Instantly go to any directory or file path from anywhere.
    Usage:
      goto <path>
    Examples:
      goto /Users/owena
      goto ../Desktop
      goto C:\\Projects\\MyApp
    """
    import os

    if not args:
        print("Usage: goto <path>")
        return

    target = args[0]

    # Expand things like ~ or relative paths
    target_path = os.path.expanduser(target)
    target_path = os.path.abspath(target_path)

    if not os.path.exists(target_path):
        print(f"❌ Path not found: {target_path}")
        return

    if os.path.isdir(target_path):
        try:
            os.chdir(target_path)
            print(f"📁 Changed directory to: {target_path}")
        except Exception as e:
            print(f"⚠️ Error changing directory: {e}")
    else:
        print(f"📄 Target is a file: {target_path}")

@register_command("root")
def root_cmd(args):
    """
    Instantly go to the root directory of the system.
    Usage:
      root
    """
    import os

    try:
        # Detect platform and set root path
        root_path = "C:\\" if os.name == "nt" else "/"
        os.chdir(root_path)
        print(f"📁 Changed directory to root: {root_path}")
    except Exception as e:
        print(f"⚠️ Error changing to root directory: {e}")
