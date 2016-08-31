# scribe-redux

This repo contains a barebones skeleton of the Scribe3 application that provides a reference framework for rapid feature development. 

## Running in a VM

Running inside a virtualized environment is strongly encouraged. To this end, a Vagrantfile is included. Run with 

        vagrant up

and the provisioning script will take care of setting up the environment for you. 

The VM is set up to share the folder in /vagrant, so your changes are immediately reflected. From the VM GUI, you can thus run with:

		cd /vagrant
		python scribe.py

## Setting up from scratch

Install the dependencies you'll need to compile Cython, plus pip and git if you don't already have them

        sudo apt-get install build-essential python-dev python-pip git libssl-dev

Install pygame as follows

        sudo apt-get build-dep python-pygame
        sudo apt-get install python-pygame
        
Install *Cython 0.20.1* and *numpy* :

        sudo pip install numpy
        sudo pip install Cython==0.20.1

It's very important that you install this specific Cython version and that you do so before running

		pip install -r requirements.txt

which will install kivy 1.8.0. No other version is allowed. 

You are now ready to launch with

		python scribe.py

### Note about virtualenv

If you wish to run this program in a virtualenv, you have to decide how many of the previous dependencies do you want to incorporate. You have to consider that
*Cython 0.20.1* is an hard requirement for this software to execute and must be installed system-wide. 

It is however possible to install *kivy* inside virtualenv. Instructions refer 
to those [provided by kivy](http://kivy.org/docs/installation/installation-linux.html#installation-in-a-virtual-environment-with-system-site-packages). 

        # Initialize virtualenv
        virtualenv -p python2.7 --system-site-packages venv
        
Note on ***pygame***: Please note that *Pygame* is more easily installed from apt and not included in the *pip*requirements file. This is because there seem to be some [issues](https://bitbucket.org/pygame/pygame/issue/140/pip-install-pygame-fails-on-ubuntu-1204) and hurdles with installing *pygame* within a virtualenv. Should you want to install it with *pip*, you should note that the package is not present in *pypy* and you need to install it from [bitbucket](https://bitbucket.org/pygame/pygame)) by following [these instructions](http://askubuntu.com/questions/299950/how-do-i-install-pygame-in-virtualenv/299965#299965) or use [this script](https://gist.github.com/brousch/6395214#file-install_pygame-sh-L4). 

Activate your virtualenv before running as above:

        source venv/bin/activate


## Guidelines

- Changes are to be made in folders, one per feature. "dowewantit" contains the skeleton for the feature that consumes our Do We Want It API. 
- KV files must be used. 
- The main widget structure that mimics the real Scribe3 application should not be touched, and changes should be self-contained to new widgets.


