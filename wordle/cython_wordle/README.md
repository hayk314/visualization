# Quick guide on compiling the cython version
<h1>What is this?</h1>

This is an experimental version of the [wordle program](https://github.com/hayk314/visualization/tree/master/wordle) but using **cython** at certain places of the code.
The part of the code working with spirals and parts of checking word collisions were slightly modified to become cython modules (to be compiled to C eventually). By introducing static types whenever possible, allows for a certain speed-up in the execution.


<h2>The usage</h2>

To run the program, one needs to compile the code first (needs the standard `gcc` compiler). From the terminal window navigate to this folder and run the following command

    python setup.py build_ext --inplace

This will build the .pyx (cython) modules. After successful build, from terminal try

    python wordle.py --filepath sample.txt 
	
which will build a wordle image from sample.txt file.
