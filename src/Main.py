#!/usr/bin/env python3

import argparse
import sys
import os

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'../../pardus_domain_core')))

from pardus_domain_core import domain_operations
from pardus_domain_core import config_manager
from pardus_domain_core import domain_joiner_realmd
from pardus_domain_core import domain_joiner_winbind

import locale
from locale import gettext as _

locale.bindtextdomain('pardus-domain-cli', '/usr/share/locale')
locale.textdomain('pardus-domain-cli')

SYSTEM_LANGUAGE = os.environ.get("LANG")
locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)


def main():
    parser = argparse.ArgumentParser(description=_("Cli application for pardus domain joiner. You must run it with sudo"))
    
    parser.add_argument("-s", "--sssd", action="store_true", help=_("Use sssd service for domain operations"))
    parser.add_argument("-w", "--winbind", action="store_true", help=_("Use winbind service for domain operations"))
    parser.add_argument("-i", "--info", action="store_true", help=_("Discover domain name"))
    parser.add_argument("--set-hostname", action="store_true", help=_("Change hostname"))

    parser.add_argument("-j", "--join", action="store_true", help=_("Join to the domain"))
    parser.add_argument("-l", "--leave", action="store_true", help=_("Leave from the domain"))
    parser.add_argument("--list", action="store_true", help=_("Check if it is in the domain"))
    parser.add_argument("--discover", action="store_true", help=_("Discover if there is a domain name"))
    # parser.add_argument("--permit", action="store_true", help=_("For sssd service"))
    # parser.add_argument("--deny", action="store_true", help=_("For sssd service"))
    # parser.add_argument("--list-users", action="store_true", help=_("For winbind service"))
    # parser.add_argument("--list-groups", action="store_true", help=_("For winbind service"))
  
    parser.add_argument("-d", "--domain", help=_("Domain name"))
    parser.add_argument("-u", "--user", help=_("Domain username"))
    parser.add_argument("-p", "--password", help=_("Domain user's password"))
    parser.add_argument("-c", "--computer-name", help=_("Computer name"))
    parser.add_argument("-ou", "--organizational-unit", help=_("Organizational unit"))

    args = parser.parse_args()

    domain = args.domain
    comp_name = args.computer_name
    username = args.user
    password = args.password
    ouaddress = args.organizational_unit

    if args.sssd:
        print(_("You have selected the sssd service."))
        if args.join:
            print(_("Join process is starting."))
            check_args(domain, comp_name, username, password)
            domain_operations.join(comp_name, domain, username, password, ouaddress, realmd=True)
        elif args.leave:
            print(_("Leave process is starting."))
            domain_operations.leave(realmd=True)
        elif args.list:
            print(domain_operations.list(realmd=True))
        elif args.discover:
            if domain is None:
                print(_("Please enter domain name!"))
                sys.exit(1)
            domain_joiner_realmd.discover(domain)
        elif args.permit:
            domain_joiner_realmd.permit()
        elif args.deny:
            domain_joiner_realmd.deny()
        else:
            parser.print_help()
            print(_("Select the action you want to perform!"))
    elif args.winbind:
        print(_("You have selected the winbind service."))
        if args.join:
            print(_("Join process is starting."))
            check_args(domain, comp_name, username, password)
            domain_operations.join(comp_name, domain, username, password, ouaddress, winbind=True)
        elif args.leave:
            print(_("Leave process is starting."))
            if username is None or password is None:
                print(_("Please enter username and password!"))
                sys.exit(1)
            domain_operations.leave(winbind=True, user=username, password=password)
        elif args.list:
            domain_operations.list(winbind=True)
        elif args.discover:
            domain_joiner_winbind.discover()
        elif args.list_users:
            result = domain_joiner_winbind.list_users()
            print(result.stdout.decode('utf-8'))
        elif args.list_groups:
            result = domain_joiner_winbind.list_group()
        else:
            parser.print_help()
            print(_("Select the action you want to perform!"))
    elif args.info:
        print(_("Domain name is being checked."))
        if domain is None:
            print(_("Please enter domain name!"))
            sys.exit(1)
        domain_operations.discover_domain(domain)
    elif args.set_hostname:
        print(_("Hostname is being changed."))
        if comp_name is None or domain is None:
            print(_("Please enter computer name and domain name!"))
            sys.exit(1)
        config_manager.set_hostname(comp_name)
        config_manager.update_hostname_file(comp_name,domain)
    else:
        parser.print_help()
        print(_("Please specify which service to use: sssd or winbind.\nYou can use the -i option to view domain information."))
        sys.exit(1)

def check_args(domain, comp_name, username, password):
    if (domain is None or comp_name is None or username is None) and password is None:
        print(_("Error: The following arguments are required!"))
        print(_("Please enter other commands:\n"), 
            ("\t\t [-d/--domain DOMAIN] [-c/--computer-namse COMPUTER]\n"),
            ("\t\t [-u/--user USERNAME] [-ou/--organizational-unit \"ou=Computers\"]\n"),
            ("\t\t [--password PASSWORD]\n"))
        sys.exit(1)


if __name__ == "__main__":
    main()
