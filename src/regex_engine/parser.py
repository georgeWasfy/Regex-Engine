def getPresedence(op):
    opPresedence = {"(": 1, "|": 2, "#": 3, "?":6, "*":6, "+": 6, "^": 5, "$": 5}    
    if op in opPresedence:
        return opPresedence[op]
    else:
        return max(opPresedence.values()) + 1
    
def implicitConcat(regex):
    output = regex[0]
    i = 1
    while(i < len(regex)):
        match regex[i]:
            case char if char in (")", "+", "*", "|", "?"):
                output += regex[i]
            case _:
                if(regex[i-1] == "(" or regex[i-1] == "|"):
                    output += regex[i]
                else:
                    output += "#" + regex[i]
        i +=1
    return output

def plus_to_star(regex):
    i = 1
    output = regex[0]
    while(i < len(regex)):
        match regex[i]:
            case "+":
                prev_symbol = regex[i - 1]
                if(prev_symbol == ')'):
                    end = i - 1
                    start = i - 1
                    while (prev_symbol != "("):
                        start -= 1
                        prev_symbol = regex[start]
                    output += regex[start: end + 1] + "*"
                else:
                    output += prev_symbol + "*"
            case _:
                output += regex[i]
        i +=1
    return output
        
    
def infix2Postfix(regex):
    stack = []
    output = ""
    for char in regex:
        match char:
            case "(":
                stack.append(char)
            case ")":
                while(len(stack) and stack[-1] != '('):
                    output += stack.pop()
                stack.pop()
            case _:
                while(len(stack)):
                    if(getPresedence(stack[-1]) >= getPresedence(char)):
                        output += stack.pop()
                    else: break
                stack.append(char)
                    
    while (len(stack)):
            if (stack[-1] == '(' or stack[-1] == ')'):
                raise ValueError(f"Invalid Expression: Open parenthesis without closing")
            output += stack.pop()
    return output

def pre_process_regex(regex: str) -> str:
    return infix2Postfix(implicitConcat(plus_to_star(regex)))
