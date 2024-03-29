from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [
    Extension("bbox", ["bbox.pyx"]),
    Extension("spirals", ["spirals.pyx"]),
]

setup(
    name='wordle',
    cmdclass={'build_ext': build_ext},
    ext_modules=ext_modules,
)

# from terminal run the following command for cythonization
# python setup.py build_ext --inplace
