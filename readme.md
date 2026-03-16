# Regex Engine Implementation

An educational implementation of a regular expression engine that demonstrates how regex patterns are processed and matched internally. This project implements a simplified regex engine using Non-deterministic Finite Automata (NFA) theory.

## Table of Contents

- [Overview](#overview)
- [How Regex Engines Work](#how-regex-engines-work)
  - [Regex Building Blocks](#regex-building-blocks)
  - [From Regex to NFA](#from-regex-to-nfa)
  - [Thompson's Construction](#thompsons-construction)
  - [Shunting Yard Algorithm](#shunting-yard-algorithm)
- [Project Structure](#project-structure)
- [Running the Code](#running-the-code)
  - [Using the Jupyter Notebook](#using-the-jupyter-notebook)
  - [Using the Python Modules](#using-the-python-modules)
- [Running Tests](#running-tests)
- [Supported Regex Features](#supported-regex-features)
- [Examples](#examples)

## Overview

This repository contains a simplified, illustrative regex engine that demonstrates the core concepts behind how regular expressions are processed. While it does not represent a fully compliant regex engine, it provides a solid foundation for understanding:

- How regex patterns are parsed and converted to intermediate representations
- How NFAs (Non-deterministic Finite Automata) are constructed from regex patterns
- How the NFA simulation matches input strings against patterns

## How Regex Engines Work

### Regex Building Blocks

Regular expressions are composed of several fundamental elements:

| Element | Description | Example |
|---------|-------------|---------|
| **Metacharacters** | Special symbols that define patterns | `.`, `\w`, `\d`, `\s` |
| **Quantifiers** | Control repetition | `*`, `+`, `?`, `{n,m}` |
| **Character Classes** | Define sets of characters | `[a-z]`, `[0-9]`, `[^abc]` |
| **Grouping** | Create sub-patterns | `()` |
| **Anchors** | Match positions | `^`, `$` |
| **Alternation** | OR operator | `a\|b` |

### From Regex to NFA

An NFA (Non-deterministic Finite Automata) is a state machine that accepts or rejects strings based on defined transitions. Converting a regex to an NFA provides a visual and computational representation of the pattern.

An NFA consists of:
- **States (Q)**: A set of states in the machine
- **Alphabet (Σ)**: The input alphabet
- **Transition Function (δ)**: `δ: Q × (Σ ∪ {ε}) → P(Q)` - returns a set of possible next states (P(Q) is the power set)
- **Start State (q₀)**: The initial state
- **Accept States (F)**: States where the string is accepted

The ε (epsilon) represents an empty string transition - a transition that doesn't consume any input.

### Thompson's Construction

Thompson's Construction is a common algorithm for converting a regex to an NFA. It builds the NFA step-by-step based on the regex operators.

#### Union Construction (a|b)

To create a union NFA for `a|b`:
1. Create new start state (State 0) and accept state (State 5)
2. Add ε-transitions from State 0 to both NFA starts
3. Add ε-transitions from both NFA accepts to State 5

```
|     | 0     | 1     | 2     | 3     | 4     | 5     |
|-----|-------|-------|-------|-------|-------|-------|
| a   | {}    | {2}   | {}    | {}    | {}    | {}    |
| b   | {}    | {}    | {}    | {4}   | {}    | {}    |
| ε   | {1, 3}| {}    | {5}   | {}    | {5}   | {}    |
```

#### Star Construction (a*)

To create a Kleene star NFA for `a*`:
1. Create new start state (State 0) and accept state (State 3)
2. Add ε-transition from State 0 to State 1 (original start)
3. Add ε-transition from State 0 to State 3 (accept directly - matches empty string)
4. Add ε-transition from State 2 (original accept) back to State 1
5. Add ε-transition from State 2 to State 3

```
|     | 0   | 1   | 2   | 3   |
|-----|-----|-----|-----|-----|
| a   | {}  | {2} | {}  | {}  |
| ε   | {1,3}| {}  | {1,3}| {}  |
```

### Shunting Yard Algorithm

The Shunting Yard algorithm transforms infix regex notation (like `a+b*c`) into postfix notation (Reverse Polish Notation - RPN), which is easier for machines to evaluate.

**Example conversions:**
| Infix | Postfix |
|-------|---------|
| `a?b#` | `a?b#` (concatenation marked with `#`) |
| `(aaba)+` | `(aaba)*` (plus converted to star) |
| `a+b*c` | `abc*+` |

The algorithm uses operator precedence:
1. Parentheses `()`
2. Alternation `|`
3. Concatenation `#`
4. Quantifiers `*`, `+`, `?`
5. Anchors `^`, `$`

## Project Structure

```
Regex-Engine/
├── regex-engine.ipynb    # Jupyter notebook with examples and explanations
├── src/                  # Source code (if modularized)
├── tests/                # Test files
│   ├── test_builder.py   # Tests for NFA builder
│   ├── test_nfa.py       # Tests for NFA engine
│   └── test_parser.py    # Tests for parser
└── readme.md             # This file
```

## Running the Code

### Using the Jupyter Notebook

The easiest way to explore the regex engine is through the Jupyter notebook:

```bash
# Install Jupyter if needed
pip install jupyter

# Start Jupyter
jupyter notebook regex-engine.ipynb
```

The notebook contains:
1. NFA representation classes
2. Regex to NFA conversion using Thompson's Construction
3. Shunting Yard algorithm implementation
4. Interactive examples showing how patterns match

### Using the Python Modules

Import and use the engine in your Python code:

```python
from your_module import EngineNFA, NFABuilder, pre_process_regex

# Define your alphabet
alphabet = {chr(i): i - ord('a') for i in range(ord('a'), ord('c') + 1)}

# Convert regex to postfix
postfix = pre_process_regex("a.b")

# Build the NFA
builder = NFABuilder(alphabet, postfix)
nfa = builder.build_nfa()

# Test for matches
result = nfa.is_match("ab")
print(result)  # True
```

## Running Tests

Run the test suite using pytest:

```bash
# Run all tests
PYTHONPATH=src pytest tests/ -v

# Run specific test files
PYTHONPATH=src pytest tests/test_builder.py -v
PYTHONPATH=src pytest tests/test_nfa.py -v
PYTHONPATH=src pytest tests/test_parser.py -v
```

## Supported Regex Features

This implementation supports the following regex features:

| Feature | Syntax | Description |
|---------|--------|--------------|
| Single character | `a`, `b` | Match exact character |
| Concatenation | `ab` | Match 'a' followed by 'b' |
| Alternation | `a\|b` | Match 'a' OR 'b' |
| Kleene Star | `a*` | Match zero or more 'a' |
| Plus | `a+` | Match one or more 'a' |
| Optional | `a?` | Match zero or one 'a' |
| Wildcard | `.` | Match any single character |
| Grouping | `(ab)` | Group patterns |

## Examples

### Basic Character Matching

```python
# Build NFA for pattern "ab"
alphabet = {'a': 0, 'b': 1}
postfix = 'ab#'  # Converted from infix
builder = NFABuilder(alphabet, postfix)
nfa = builder.build_nfa()

nfa.is_match(['a', 'b'])  # True
nfa.is_match(['a'])       # False
```

### Using Alternation

```python
# Pattern: a|b (match 'a' or 'b')
postfix = 'ab|'
nfa = NFABuilder(alphabet, postfix).build_nfa()

nfa.is_match(['a'])  # True
nfa.is_match(['b'])  # True
nfa.is_match(['c'])  # False
```

### Kleene Star (Zero or More)

```python
# Pattern: a* (zero or more 'a')
postfix = 'a*'
nfa = NFABuilder(alphabet, postfix).build_nfa()

nfa.is_match([])      # True (empty string)
nfa.is_match(['a'])   # True
nfa.is_match(['a', 'a', 'a'])  # True
```

### Optional (Zero or One)

```python
# Pattern: a? (zero or one 'a')
postfix = 'a?'
nfa = NFABuilder(alphabet, postfix).build_nfa()

nfa.is_match([])    # True
nfa.is_match(['a']) # True
nfa.is_match(['b']) # False
```

## License

MIT License
