import os
import sys
import math
import traceback

VERSION = 2

math_functions = {
    "COS": math.cos,
    "SIN": math.sin,
    "TAN": math.tan,
    "ACOS": math.acos,
    "ASIN": math.asin,
    "ATAN": math.atan,
    "COSH": math.cosh,
    "SINH": math.sinh,
    "TANH": math.tanh,
    "ACOSH": math.acosh,
    "ASINH": math.asinh,
    "ATANH": math.atanh,
    "DEG": math.degrees,
    "RAD": math.radians,
    "ABS": math.fabs,
    "SQRT": math.sqrt,
    "LOG": math.log,
    "LOG2": math.log2,
    "LOG10": math.log10,
    "EXP": math.exp,
    "ROUND": lambda x: float(round(x)),
    "CEIL": lambda x: float(math.ceil(x)),
    "FLOOR": lambda x: float(math.floor(x))
}

reserved = [
    "LET", "PRINT", "INPUT", "IF", "GOTO",
    "SLEEP", "END", "LIST", "REM", "READ",
    "WRITE", "APPEND", "RUN", "CLS", "CLEAR",
    "EXIT", "LOAD", "SAVE", "THEN", "ELSE",
    "FOR", "TO", "DO", "GOSUB", "RETURN",
    "STA", "STS", "STT", "LDA", "LDS", "LDT", "DIR"
]

registers = {
    "A": 0,
    "S": 0,
    "T": 0,
}

operators = [
    ["==", "!=", ">", "<", ">=", "<="],
    ["<<", ">>"],
    ["."],
    ["+", "-"],
    ["*", "/", "&", "|", "%"],
    ["^"],
    ["!"] + list(math_functions.keys())
]

constants = {
    "PI": math.pi,
    "E": math.e,
    "TAU": math.tau,
}

lines = {}
maxLine = 0
linePointer = 0
stopExecution = False
# change identifiers to be a list of set, in order to call subroutine
identifiers = [{}]
returnPos = []
printReady = True

def main():
    global stopExecution
    print(f"Tiny BASIC version {VERSION}\nby Jeffrey Chen")
    print("\n<Based on Tiny BASIC version 1 by Chung-Yuan Huang>\n")
    while True:
            try:
                if printReady:
                    # not a bug fixed, just prefer this way
                    print(">>>", end=" ")
                nextLine = input()
                if len(nextLine) > 0:
                    executeTokens(lex(nextLine))
                    # bug fixed: reset stopExecution when a command is done
                    stopExecution = False
            except KeyboardInterrupt:
                pass
            except EOFError:
                print("Bye!")
                break
            except SystemExit:
                print("Bye!")
                break
            except Exception as e: # show traceback when error occurs
                error_class = e.__class__.__name__ #取得錯誤類型
                detail = e.args[0] #取得詳細內容
                cl, exc, tb = sys.exc_info() #取得Call Stack
                lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
                fileName = lastCallStack[0] #取得發生的檔案名稱
                lineNum = lastCallStack[1] #取得發生的行號
                funcName = lastCallStack[2] #取得發生的函數名稱
                errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
                print("\nExecution halted:\n"+errMsg)

def clearLines(): # clear all codes
    global lines, maxLine
    lines = {}
    maxLine = 0

def resetExcution(): # reset all variables and registers
    global identifiers, returnPos, registers
    identifiers = [{}]
    returnPos = []
    registers = {
        "A": 0,
        "S": 0,
        "T": 0,
    }

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def getVarType(token):
    if len(token) > 1:
        if token[-1] == "$":
            return "STRING"
    return "NUM"

def isValidIdentifier(token):
    if len(token) == 0:
        return False
    if len(token) > 1:
        if token[-1] == "$":
            token = token[0:-1]
    if not (token[0].lower() in "abcdefghijklmnopqrstuvwxyz_"):
        return False
    for c in token[1:]:
        # bug fixed: token[0].lower() -> c.lower()
        if not (c.lower() in "abcdefghijklmnopqrstuvwxyz0123456789_"):
            return False
    return True
    
def lex(line):
    # Splitteo la linea en varios tokens  # split line into tokens
    inString = False
    tokens = []
    currentToken = ""
    line = line + " "
    for c in line:
        if not(inString) and c in " \"":
            if len(currentToken) != 0:
                tokens.append([currentToken, "TBD"])   # To Be Decide?
                currentToken = ""
            if c == '"':
                inString = True
        elif inString and c == '"':
            tokens.append([currentToken, "STRING"])
            currentToken = ""
            inString = False
        # to make expressions like "(1 + 2) * 3" work
        # parentesis don't have to separate with other tokens by spaces
        elif c in ['(', ')']:
            if len(currentToken) != 0:
                tokens.append([currentToken, "TBD"])
                currentToken = ""
            tokens.append([c, "PAREN"]) # parentesis
        else:
            currentToken += c

    # Le asigno un tipo a cada token (assign a type to each token)
    for token in tokens:
        if token[1] != "TBD":
            continue
        value = token[0]
        if is_number(value):
            token[0] = float(token[0])
            token[1] = "NUM" #Number
        elif value.upper() in reserved:
            token[0] = value.upper()
            token[1] = "RESVD" #Reserved word
        elif value in constants:
            token[0] = constants[value.upper()]
            token[1] = "NUM" #built-in constant
        elif value == "=":
            token[1] = "ASGN"
        elif isValidIdentifier(token[0]) and token[0] not in math_functions:
            token[1] = "ID" #Identifier
        else:
            for operator in operators:
                if token[0] in operator:
                    token[1] = "OP"
    #print(tokens)
    return tokens

def executeTokens(tokens):
    global lines, maxLine, stopExecution, linePointer, printReady, identifiers, returnPos
    printReady = True
    if tokens[0][1] == "NUM":
        lineNumber = int(tokens.pop(0)[0])
        if len(tokens) != 0:
            lines[lineNumber] = tokens
            if lineNumber > maxLine:
                maxLine = lineNumber
        else:
            lines.pop(lineNumber, None)
        return
    if tokens[0][1] != "RESVD":
        # bug fixed: stopExecution when run into a non-reserved word
        stopExecution = True
        print(f"Error: Unknown command {tokens[0]}.")
    else:
        command = tokens[0][0]
        if command == "REM":
            return
        elif command == "CLS":
            print("\n"*500)
        elif command == "END":
            stopExecution = True
        elif command == "EXIT":
            quit()
        elif command == "CLEAR":
            clearLines()
            resetExcution()
        elif command == "DIR": # list all the variables and their values in the current scope
            print(identifiers[0])
        elif command == "LIST":
            i = 0
            while i <= maxLine:
                if i in lines:
                    line = str(i)
                    for token in lines[i]:
                        tokenVal = ""
                        if token[1] == "NUM":
                            tokenVal = getNumberPrintFormat(token[0])
                        elif token[1] == "STRING":
                            tokenVal = f"\"{token[0]}\""
                        else:
                            tokenVal = token[0]
                        line += " " + str(tokenVal)
                    print(line)
                i = i + 1
        elif command == "PRINT":
            if not(printHandler(tokens[1:])): stopExecution = True
        elif command == "LET":
            if not(letHandler(tokens[1:])): stopExecution = True
        elif command == "INPUT":
            if not(inputHandler(tokens[1:])): stopExecution = True
        elif command == "GOTO":
            if not(gotoHandler(tokens[1:])): stopExecution = True
        elif command == "IF":
            if not(ifHandler(tokens[1:])): stopExecution = True
        elif command == "FOR":
            if not(forHandler(tokens[1:])): stopExecution = True
        elif command == "RUN":
            linePointer = 0
            # bug fixed: clear identifiers before execution
            resetExcution()
            while linePointer <= maxLine:
                if linePointer in lines:
                    executeTokens(lines[linePointer])
                    if stopExecution:
                        stopExecution = False
                        break
                linePointer = linePointer + 1
            # bug fixed: clear identifiers after execution
            resetExcution()
        elif command == "SAVE":
            if not(saveHandler(tokens[1:])): stopExecution = True
        elif command == "LOAD":
            if not(loadHandler(tokens[1:])): stopExecution = True
        elif command == "GOSUB":
            if not(gosubHandler(tokens[1:])): stopExecution = True
        elif command == "RETURN":
            if len(tokens) != 1:
                print("Error: Invalid return command.")
                stopExecution = True
            if not(returnHandler()): stopExecution = True
        elif command == "STA":
            if not(staHandler(tokens[1:])): stopExecution = True
        elif command == "LDA":
            if not(ldaHandler(tokens[1:])): stopExecution = True
        elif command == "STS":
            if not(stsHandler(tokens[1:])): stopExecution = True
        elif command == "LDS":
            if not(ldsHandler(tokens[1:])): stopExecution = True
        elif command == "STT":
            if not(sttHandler(tokens[1:])): stopExecution = True
        elif command == "LDT":
            if not(ldtHandler(tokens[1:])): stopExecution = True


def getNumberPrintFormat(num):
    if int(num) == float(num):
        return int(num)
    return num

def saveHandler(tokens):
    global lines, maxLine, printReady
    printReady = True
    if len(tokens) != 1:
        print("Error: Invalid arguments.")
        return False
    if tokens[0][1] != "STRING":
        print("Error: Invalid filename.")
        return False
    filename = tokens[0][0]
    # if file extension not specified, add .tb
    if '.' not in filename:
        filename = filename + '.tb'
    # if the file already exists, ask the user if he wants to overwrite it
    if os.path.isfile(filename):
        overwrite = input(f"File {filename} already exists. Overwrite? (y/n)")
        if overwrite.lower() != "y":
            return False
    with open(filename, 'w') as f:
        # basicly copy from "LIST" command
        for i in range(maxLine + 1):
            if i in lines:
                line = str(i)
                for token in lines[i]:
                    tokenVal = ""
                    if token[1] == "NUM":
                        tokenVal = getNumberPrintFormat(token[0])
                    elif token[1] == "STRING":
                        tokenVal = f"\"{token[0]}\""
                    else:
                        tokenVal = token[0]
                    line += " " + str(tokenVal)
                f.write(line + "\n")
    return True

def loadHandler(tokens):
    global lines, maxLine, printReady
    printReady = True
    if len(tokens) != 1:
        print("Error: Invalid arguments.")
        return False
    if tokens[0][1] != "STRING":
        print("Error: Invalid filename.")
        return False
    filename = tokens[0][0]
    # if file extension not specified, add .tb
    if '.' not in filename:
        filename = filename + '.tb'
    try:
        with open(filename, 'r') as f:
            # basicly copy from "if tokens[0][1] == "NUM":" in executeTokens()
            clearLines()
            for line in f:
                tokens = lex(line.strip())
                if len(tokens) == 0:
                    continue
                if tokens[0][1] == "NUM":
                    lineNumber = int(tokens.pop(0)[0])
                    if len(tokens) != 0:
                        lines[lineNumber] = tokens
                        if lineNumber > maxLine:
                            maxLine = lineNumber
                    else:
                        lines.pop(lineNumber, None)
                else:
                    print("Error: Invalid line number.")
                    return False
    except FileNotFoundError:
        print("Error: File not found.")
        return False
    return True

def gotoHandler(tokens):
    global linePointer
    if len(tokens) == 0:
        print("Error: Expected expression.")
        return
    newNumber = solveExpression(tokens, 0)
    if newNumber[1] != "NUM":
        print("Error: Line number expected.")
    else:
        linePointer = newNumber[0] - 1
    return True

def gosubHandler(tokens):
    global linePointer, identifiers, returnPos
    if len(tokens) == 0:
        print("Error: Expected expression.")
        return
    newNumber = solveExpression(tokens, 0)
    if newNumber[1] != "NUM":
        print("Error: Line number expected.")
    else:
        returnPos.insert(0, linePointer) # push current line number to stack
        identifiers.insert(0, {}) # variable scope for subroutine
        linePointer = newNumber[0] - 1 # jump to subroutine
    return True

def returnHandler():
    global linePointer, identifiers, returnPos
    if len(returnPos) == 0:
        print("Error: Not in a subroutine.")
        return
    linePointer = returnPos.pop(0) # pop current line number from stack
    identifiers.pop(0)
    return True

def inputHandler(tokens):
    varName = None
    if len(tokens) == 0:
        print("Error: Expected identifier.")
        return
    elif len(tokens) == 1 and tokens[0][1] == "ID":
        varName = tokens[0][0]
    else:
        varName = solveExpression(tokens, 0)[0]
        if not(isValidIdentifier(varName)):
            print(f"Error: {varName} is not a valid identifier.")
            return
    while True:
        print("?", end = '')
        varValue = input()
        if getVarType(varName) == "STRING":
            identifiers[0][varName] = [varValue, "STRING"]
            break
        else:
            if is_number(varValue):
                # bug fixed: varValue -> float(varValue)
                identifiers[0][varName] = [float(varValue), "NUM"] 
                break
            else:
                print("Try again.")
    return True

def ifHandler(tokens):
    thenPos = elsePos = None
    for i in range(0, len(tokens)):
        if tokens[i] == ["THEN", "RESVD"]: # THEN is change to be a reserved word
            thenPos = i
            break
    for i in range(0, len(tokens)): # find the position of "ELSE"
        if tokens[i] == ["ELSE", "RESVD"]:
            elsePos = i
            break
    # if "THEN" is not found or "ELSE" is found before "THEN"
    if thenPos == None or (elsePos and thenPos > elsePos): 
        print("Error: Malformed IF statement.")
        return
    exprValue = solveExpression(tokens[0:thenPos], 0)
    if exprValue == None:
        return
    elif exprValue[0] != 0:
        if len(tokens[thenPos+1:elsePos]) == 0:
            print("Error: Malformed IF statement.")
            return      
        executeTokens(tokens[thenPos+1:elsePos])
    # if "ELSE" is found, and exprValue is False
    # execute the expression after "ELSE"
    elif elsePos: 
        if len(tokens[elsePos+1:]) == 0:
            print("Error: Malformed IF statement.")
            return
        executeTokens(tokens[elsePos+1:])
    return True

def forHandler(tokens):
    global identifiers
    toPos = doPos = None
    # find the position of "TO" and "DO"
    for i in range(0, len(tokens)):
        if tokens[i] == ["TO", "RESVD"]:
            toPos = i
            break
    for i in range(0, len(tokens)):
        if tokens[i] == ["DO", "RESVD"]:
            doPos = i
            break
    if toPos == None or doPos == None or toPos > doPos:
        print("Error: Malformed FOR statement.")
        return 
    # get a copy of global variables
    globalIdentifiers = identifiers[0].copy()
    # set the iterator to the first value
    executeTokens([["LET", "RESVD"]] + tokens[0:toPos])
    # calculate the end value
    endValue = solveExpression(tokens[toPos+1:doPos], 0)
    if endValue == None:
        return
    if endValue[1] != "NUM":
        print("Error: Expected number.")
        return
    endValue = endValue[0]
    # execute the FOR statement
    while getIdentifierValue(tokens[0][0])[0] <= endValue:
        executeTokens(tokens[doPos+1:])
        tokens[toPos - 1][0] += 1
        executeTokens([["LET", "RESVD"]] + tokens[0:toPos])
    # restore the global variables
    identifiers[0] = globalIdentifiers
    return True

def letHandler(tokens):
    varName = None
    varValue = None
    eqPos = None
    for i in range(0, len(tokens)):
        if tokens[i][1] == "ASGN":
            eqPos = i
            break
    if eqPos == None:
        print("Error: Malformed LET statement.")
        return
    if eqPos == 1 and tokens[0][1] == "ID":
        varName = tokens[0][0]
    else:
        if len(tokens[0:i]) == 0:
            print("Error: Expected identifier.")
            return
        varName = solveExpression(tokens[0:i], 0)
        if varName == None:
            stopExecution = True
            return
        varName = varName[0]
        if not(isValidIdentifier(varName)):
            print(f"Error: {varName} is not a valid identifier.")
            return
    if len(tokens[i+1:]) == 0:
        print("Error: Expected expression.")
        return
    varValue = solveExpression(tokens[i+1:], 0)
    if varValue == None:
        return
    if getVarType(varName) != varValue[1]:
        print(f"Error: Variable {varName} type mismatch.")
        return
    identifiers[0][varName] = varValue
    return True

def printHandler(tokens):
    if len(tokens) == 0:
        print("Error: Expected identifier.")
        return
    exprRes = solveExpression(tokens, 0)
    if exprRes == None:
        return
    # bug fixed: print out a number will cause it convert to int
    value = exprRes[0]
    if exprRes[1] == "NUM":
        value = getNumberPrintFormat(value)
    print(value)
    return True

# store number to rigister A
def staHandler(tokens):
    global registers
    if len(tokens) == 0:
        print("Error: Expected identifier.")
        return
    exprRes = solveExpression(tokens, 0)
    if exprRes == None:
        return
    if exprRes[1] != "NUM":
        print("Error: Rigister A expected number.")
        return
    registers["A"] = exprRes[0]
    return True

def stsHandler(tokens):
    global registers
    if len(tokens) == 0:
        print("Error: Expected identifier.")
        return
    exprRes = solveExpression(tokens, 0)
    if exprRes == None:
        return
    if exprRes[1] != "NUM":
        print("Error: Rigister A expected number.")
        return
    registers["S"] = exprRes[0]
    return True

def sttHandler(tokens):
    global registers
    if len(tokens) == 0:
        print("Error: Expected identifier.")
        return
    exprRes = solveExpression(tokens, 0)
    if exprRes == None:
        return
    if exprRes[1] != "NUM":
        print("Error: Rigister A expected number.")
        return
    registers["T"] = exprRes[0]
    return True

# load number from rigister A
def ldaHandler(tokens):
    global registers
    varName = None
    if len(tokens) == 0:
        print("Error: Expected identifier.")
        return
    elif len(tokens) == 1 and tokens[0][1] == "ID":
        varName = tokens[0][0]
    else:
        varName = solveExpression(tokens, 0)[0]
        if not(isValidIdentifier(varName)):
            print(f"Error: {varName} is not a valid identifier.")
            return
    if getVarType(varName) != "NUM":
        print(f"Error: Variable {varName} is not a number.")
        return
    executeTokens([["LET", "RESVD"], [varName, "ID"], ["=", "ASGN"], [registers["A"], "NUM"]])
    return True

def ldsHandler(tokens):
    global registers
    varName = None
    if len(tokens) == 0:
        print("Error: Expected identifier.")
        return
    elif len(tokens) == 1 and tokens[0][1] == "ID":
        varName = tokens[0][0]
    else:
        varName = solveExpression(tokens, 0)[0]
        if not(isValidIdentifier(varName)):
            print(f"Error: {varName} is not a valid identifier.")
            return
    if getVarType(varName) != "NUM":
        print(f"Error: Variable {varName} is not a number.")
        return
    executeTokens([["LET", "RESVD"], [varName, "ID"], ["=", "ASGN"], [registers["S"], "NUM"]])
    return True

def ldtHandler(tokens):
    global registers
    varName = None
    if len(tokens) == 0:
        print("Error: Expected identifier.")
        return
    elif len(tokens) == 1 and tokens[0][1] == "ID":
        varName = tokens[0][0]
    else:
        varName = solveExpression(tokens, 0)[0]
        if not(isValidIdentifier(varName)):
            print(f"Error: {varName} is not a valid identifier.")
            return
    if getVarType(varName) != "NUM":
        print(f"Error: Variable {varName} is not a number.")
        return
    executeTokens([["LET", "RESVD"], [varName, "ID"], ["=", "ASGN"], [registers["T"], "NUM"]])
    return True

def getIdentifierValue(name):
    return identifiers[0][name]

def solveExpression(tokens, level):
    leftSideValues = []
    rightSideValues = []
    if level < len(operators):
        i = 0
        while i < len(tokens):
            if not(tokens[i][1] in ["OP", "NUM", "STRING", "ID", 'PAREN']):
                print(f"Error: Unknown operand {tokens[i][0]}")
                return None
            elif tokens[i][1] == "PAREN":
                # find the matching close parentheses
                close = findMatchingClose(tokens, i)
                if close == None:
                    print("Error: Unmatched parentheses.")
                    return None
                # solve the expression inside the parentheses
                subExpr = solveExpression(tokens[i+1:close], 0)
                if subExpr == None:
                    return None
                leftSideValues.append(subExpr)
                # continue to the next token
                i = close
            elif tokens[i][1] == "OP" and tokens[i][0] in operators[level]:
                exprResL = None
                exprResR = None
                if len(leftSideValues) != 0:
                    exprResL = solveExpression(leftSideValues, level)
                rightSideValues = tokens[i+1:]
                if len(rightSideValues) != 0:
                    exprResR = solveExpression(rightSideValues, level)
                
                if tokens[i][0] == "+":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    elif exprResL[1] == "NUM" and exprResR[1] == "NUM":
                        return [exprResL[0] + exprResR[0], "NUM"]
                    else:
                        print("Error: Operand type mismatch.")
                        return None
                elif tokens[i][0] == "-":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    elif exprResL[1] == "NUM" and exprResR[1] == "NUM":
                        return [exprResL[0] - exprResR[0], "NUM"]
                    else:
                        print("Error: Operand type mismatch.")
                        return None
                elif tokens[i][0] == "/":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    elif exprResL[1] == "NUM" and exprResR[1] == "NUM":
                        return [exprResL[0] / exprResR[0], "NUM"]
                    else:
                        print("Error: Operand type mismatch.")
                        return None 
                elif tokens[i][0] == "*":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    elif exprResL[1] == "NUM" and exprResR[1] == "NUM":
                        return [exprResL[0] * exprResR[0], "NUM"]
                    else:
                        print("Error: Operand type mismatch.")
                        return None     
                elif tokens[i][0] == "^":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    elif exprResL[1] == "NUM" and exprResR[1] == "NUM":
                        return [exprResL[0] ** exprResR[0], "NUM"]
                    else:
                        print("Error: Operand type mismatch.")
                        return None
                elif tokens[i][0] == "%":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    elif exprResL[1] == "NUM" and exprResR[1] == "NUM":
                        return [exprResL[0] % exprResR[0], "NUM"]
                    else:
                        print("Error: Operand type mismatch.")
                        return None
                elif tokens[i][0] == "==":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    else:
                        return [exprResL[0] == exprResR[0], "NUM"]
                elif tokens[i][0] == "!=":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    else:
                        return [exprResL[0] != exprResR[0], "NUM"]
                elif tokens[i][0] == "<=":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    else:
                        return [exprResL[0] <= exprResR[0], "NUM"]
                elif tokens[i][0] == "<":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    else:
                        return [exprResL[0] < exprResR[0], "NUM"]
                elif tokens[i][0] == ">":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    else:
                        return [exprResL[0] > exprResR[0], "NUM"]
                elif tokens[i][0] == ">=":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    else:
                        return [exprResL[0] >= exprResR[0], "NUM"]
                # operator <<
                elif tokens[i][0] == "<<":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    if exprResL[1] != "NUM" or exprResR[1] != "NUM":
                        print("Error: Operand type mismatch.")
                        return None
                    if int(exprResL[0]) != exprResL[0] or int(exprResR[0]) != exprResR[0]:
                        print("Error: Operand type mismatch.")
                        return None
                    return [float(int(exprResL[0]) << int(exprResR[0])), "NUM"]
                # operator >>
                elif tokens[i][0] == ">>":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    if exprResL[1] != "NUM" or exprResR[1] != "NUM":
                        print("Error: Operand type mismatch.")
                        return None
                    if int(exprResL[0]) != exprResL[0] or int(exprResR[0]) != exprResR[0]:
                        print("Error: Operand type mismatch.")
                        return None
                    return [float(int(exprResL[0]) >> int(exprResR[0])), "NUM"]
                elif tokens[i][0] == "&":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    elif exprResL[1] == "NUM" and exprResR[1] == "NUM":
                        return [(exprResL[0]) and (exprResR[0]), "NUM"]
                    else:
                        print("Error: Operand type mismatch.")
                        return None
                elif tokens[i][0] == "|":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    elif exprResL[1] == "NUM" and exprResR[1] == "NUM":
                        return [(exprResL[0]) or (exprResR[0]), "NUM"]
                    else:
                        print("Error: Operand type mismatch.")
                        return None
                elif tokens[i][0] == ".":
                    if exprResL == None or exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    else:
                        value1 = exprResL[0]
                        if exprResL[1] == "NUM":
                            value1 = str(getNumberPrintFormat(value1))
                        value2 = exprResR[0]
                        if exprResR[1] == "NUM":
                            value2 = str(getNumberPrintFormat(value2))
                        return [value1 + value2, "STRING"]
                # operator !
                elif tokens[i][0] == "!":
                    # as an unary operator, ! only takes one argument
                    if exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    if exprResL != None:
                        print("Error: ! is an unary operator.")
                        return None
                    if exprResR[1] == "NUM":
                        return [not exprResR[0], "NUM"]
                    else:
                        print("Error: Operand type mismatch.")
                        return None
                # math function also handle as a unary operator
                elif tokens[i][0] in math_functions:
                    if exprResR == None:
                        print("Error: Operator expects value.")
                        return None
                    if exprResL != None:
                        print("Error: Function is unary operator.")
                        return None
                    if exprResR[1] == "NUM":
                        return [math_functions[tokens[i][0]](exprResR[0]), "NUM"]
                    else:
                        print("Error: Operand type mismatch.")
                        return None
            else:
                leftSideValues.append(tokens[i])
            i += 1
        return solveExpression(leftSideValues, level + 1)
    else:
        if len(tokens) > 1:
            print("Error: Operator expected.")
            return None
        elif tokens[0][1] == "ID":
            if tokens[0][0] in identifiers[0]:
                return getIdentifierValue(tokens[0][0])
            else:
                print(f"Error: Variable {tokens[0][0]} not initialized.")
                return None
        return tokens[0]

def findMatchingClose(tokens, openIndex):
    openCount = 1
    for i in range(openIndex + 1, len(tokens)):
        if tokens[i][0] == "(":
            openCount += 1
        elif tokens[i][0] == ")":
            openCount -= 1
        if openCount == 0:
            return i
    return None


if __name__ == '__main__':
    main()
