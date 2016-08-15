# scribe-redux

This repo contains a barebones skeleton of the Scribe3 application that provides a reference framework for rapid feature development. 

## Setting up

Install the dependencies you'll need to compile Cython, plus pip and git if you don't already have them

        sudo apt-get install build-essential python-dev python-pip git 

Install pygame as follows

        sudo apt-get build-dep python-pygame
        sudo apt-get install python-pygame
        
Install *Cython 0.20.1* and *numpy* :

        sudo pip install numpy
        sudo pip install Cython==0.20.1

It's very important that you install this specific Cython version and that you do so before running

		pip install -r requirements.txt

which will install kivy 1.8.1. No other version is allowed. 

You are now ready to launch with

		python scribe.py

## Guidelines

Changes are to be made in folders, one per feature. "dowewantit" contains the skeleton for the feature that consumes our Do We Want It API. 


