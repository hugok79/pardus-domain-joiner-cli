#!/bin/bash
set -e

langs=("tr")

if ! command -v xgettext &> /dev/null
then
	echo "xgettext could not be found."
	echo "you can install the package with 'apt install gettext' command on debian."
	exit
fi


echo "updating pot file"
> po/pardus-domain-cli.pot
# xgettext -o po/pardus-domain-cli.pot --files-from=po/files

for file in $(cat po/files); do
    head_line=$(head -n 1 "$file")
    if [[ "$head_line" =~ python ]]; then
        xgettext --language=Python -k_ --join-existing -o po/pardus-domain-cli.pot "$file"
    else
        xgettext --language=Shell -k_ -kgettext -keval_gettext --join-existing -o po/pardus-domain-cli.pot "$file"
    fi
done

for lang in ${langs[@]}; do
	if [[ -f po/$lang.po ]]; then
		echo "updating $lang.po"
		msgmerge -o po/$lang.po po/$lang.po po/pardus-domain-cli.pot
	else
		echo "creating $lang.po"
		cp po/pardus-domain-cli.pot po/$lang.po
	fi
done
