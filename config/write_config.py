# python 3.x
from configparser import ConfigParser

config = ConfigParser()

# get the section data from config.ini
# config.add_section("main")

# config.set("main", "EMAIL", "email")
# config.set("main", "PASSWORD", "password")

with open(file="config/config.ini", mode="w") as f:
    config.write(f)