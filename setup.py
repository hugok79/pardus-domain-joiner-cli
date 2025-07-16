#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess

from setuptools import setup, find_packages

def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            os.makedirs("{}/{}/LC_MESSAGES".format(podir, po.split(".po")[0]), exist_ok=True)
            mo_file = "{}/{}/LC_MESSAGES/{}".format(podir, po.split(".po")[0], "pardus-domain-cli.mo")
            msgfmt_cmd = 'msgfmt {} -o {}'.format(podir + "/" + po, mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(("/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                       ["po/" + po.split(".po")[0] + "/LC_MESSAGES/pardus-domain-cli.mo"]))
    return mo

changelog = "debian/changelog"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
        version = ""
    f = open("src/__version__", "w")
    f.write(version)
    f.close()


data_files = [
    (
        "/usr/share/pardus/pardus-domain-settings/pardus-domain-cli/src/",
        ["src/Main.py", "src/__version__"],
    ),
    ("/usr/bin/", ["pardus-domain-cli"]),
] + create_mo_files()

setup(
    name="pardus-domain-cli",
    version=version,
    packages=find_packages(),
    scripts=["pardus-domain-cli"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Büşra ÇAĞLIYAN",
    author_email="busra.cagliyan@pardus.org.tr",
    description="A cli applications that joins your computer to the domain or leaves it from the domain.",
    license="GPLv3",
    keywords="domain settings cli",
    url="https://www.pardus.org.tr",
)
