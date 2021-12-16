import matplotlib.pyplot as plt
import sympy as sy
import numpy as np

print('importing modules ...')
print('imported np')
sy.init_printing()
print('imported sy')
print('imported plt')


def __init_modules(module_name: str, alias_name: str):
    if alias_name not in globals():
        globals()[alias_name] = __import__(module_name)


def init_pd():
    __init_modules('pandas', 'pd')


def init_sns():
    __init_modules('seaborn', 'sns')


print('module init functions defined')
