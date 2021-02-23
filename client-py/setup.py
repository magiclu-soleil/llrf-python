"""    setup.py file for SWIG example"""
# https://zhuanlan.zhihu.com/p/30370893
from distutils.core import setup, Extension
phase_set_module = Extension('_phase_set', sources=['phase_set_wrap.c', 'phase_set.c'], )
setup(name = 'phase_set',  version = '0.1', author = "Lu_swig", description = """Simple swig example from docs""", ext_modules = [phase_set_module], py_modules = ["phase_set"] )