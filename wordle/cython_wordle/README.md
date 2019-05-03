# Quick guide on compiling the cython version
<h1>What is this?</h1>

This folder is an almost identical version of the program in the [wordle](https://github.com/hayk314/visualization/tree/master/wordle) folder but with a **cython** touch.
All in all, this is a quick attempt toward increasing the performance of the wordle program but not diverging much from python.
Thus, certain components of the code, most notably the part working with spirals, and the part implementing word placing strategy
were modified a bit to become cython modules (to be complied to C eventually). By introducing static types whenever possible, 
allows for noticeable speed-up in the code.


<h2>The usage</h2>

Before being able to run the program, one needs to compile the code (needs the standard `gcc` compiler).
From terminal window navigate to this folder and run the following command

    python setup.py build_ext --inplace

This will build the .pyx (cython) modules. After successful build, from terminal try

    python main.py sample2.txt 
	
which will build a wordle image from sample2.txt file.

<h3>The version</h3>

This is yet an experiment and will not be merged with the main code for now.
Tested on `Windows 10` and `Centos 7.5`.
