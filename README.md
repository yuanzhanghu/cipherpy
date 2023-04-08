# CipherPy

CipherPy is a Python package that obfuscates the function arguments in your Python code. This can be useful for protecting your code from reverse engineering or for making it more difficult for someone to understand what your code is doing.

## Installation

You can install CipherPy by:

```
git clone https://github.com/yuanzhanghu/cipherpy.git
```

Then, navigate to the `cipherpy` directory and install the necessary dependencies using pip:
```
pip install -r requirements.txt
```

## Usage

To obfuscate a Python file or directory, you can use the `cipherpy.py` script. 

For example, if you want to obfuscate a single file named `mycode.py`, you can run the following command:

```
python cipherpy.py myproject/mycode.py
```
Or, if you want to obfuscate a directory named myproject, you can run the following command:

```
python cipherpy.py myproject/
```
This will obfuscate all the Python files in the myproject directory. NOTES: subdirectories are not included.

# Contributing
If you find a bug or have a suggestion for a new feature, please open an issue on GitHub or submit a pull request.

# License
CipherPy is released under the MIT license. See LICENSE for more information.


