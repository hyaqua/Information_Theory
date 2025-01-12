# Information_Theory
 LZ77 and Fano code implementations in python
## Prerequisites
 - Python 3.10 or newer
## Usage
Firstly clone the repo
Then activate the python virtual environment:
### Windows
```
python3 -m venv .\.venv
.\.venv\Scripts\activate.bat    
```
### Linux / MacOS
```
python3 -m venv .\.venv
source ./.venv/bin/activate
```
### Installing python dependencies
```
pip3 install -r requirements.txt
```
In both LZ77 and Fano python files there are example usages at the ends of each file which you can use to encode or decode your files.
## Currently working
 - LZ77 with variable window size and future size (window - how far to search for an occurence of the same sequence, future - how long the sequence can be)
 - Fano with 8 bit reads and encoding of variable size
## TODO
 - Update Fano to read from 1 to 16 bits at a time
 - Update LZ77 to add a restriction of up to 30 bit integers for the window and future size (otherwise the built-in python read function brakes, and around a gigabyte at a time is more than enough for encoding)
 - Optimize LZ77 reading of files, by using built in functions instead of libraries.
 - Make both more user-friendly by adding a way to call them from the terminal.