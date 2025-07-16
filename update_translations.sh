#!/bin/bash

langs=("tr")

if ! command -v xgettext &> /dev/null
then
	echo "xgettext could not be found."
	echo "you can install the package with 'apt install gettext' command on debian."
	exit
fi


echo "updating pot file"
xgettext -o po/pardus-domain-cli.pot --files-from=po/files

for lang in ${langs[@]}; do
	if [[ -f po/$lang.po ]]; then
		echo "updating $lang.po"
		msgmerge -o po/$lang.po po/$lang.po po/pardus-domain-cli.pot
	else
		echo "creating $lang.po"
		cp po/pardus-domain-cli.pot po/$lang.po
	fi
done
