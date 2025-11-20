#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import getpass
import os
import logging
import sys

import ldap
import managers.ConfigManager as ConfigManager
from pardus_domain_joiner import domain_operations
from pardus_domain_joiner import domain_joiner_ldap

import locale
from locale import gettext as _

# Development: ../locale, Production: /usr/share/locale
localedir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../locale')
if not os.path.exists(localedir):
    localedir = '/usr/share/locale'

SYSTEM_LANGUAGE = os.environ.get("LANG")
locale.setlocale(locale.LC_ALL, os.environ.get("LANG"))

locale.bindtextdomain('pardus-domain-joiner-cli', localedir)
locale.textdomain('pardus-domain-joiner-cli')

error_patterns = {
    "ou_errors": {
        "The organizational unit does not exist": _("Invalid organizational unit!"),
        "Couldn't lookup computer container": _("Invalid organizational unit!"),
        "failed to precreate account in ou": _("Invalid organizational unit!"),
        "but is not in the desired organizational unit": _("Invalid organizational unit!")
    },
    "auth_errors": {
        "Preauthentication failed": _("Preauthentication failed!"),
        "not found in Kerberos database": _("Preauthentication failed!"),
        "The attempted logon is invalid": _("Preauthentication failed!")
    },
    "other": {
        "\"workgroup\" set to '',": 
        _("Warning: Workgroup is empty. You can set it using the --workgroup parameter.")
    }
}


class Model:
    domain = ""
    computer_name = ""
    username = ""
    password = ""
    organizational_unit = ""
    connection_type = ""
    hostname = ""


def read_config():
    config = ConfigManager.read_config()

    model = Model()
    model.username = config["username"]
    model.domain = config["domain"]
    model.connection_type = config["connection_type"]
    model.organizational_unit = config["organizational_unit"]
    model.hostname = os.uname()[1]

    return model


def save_config(model):
    config = vars(model).copy()

    config.pop("password", None)
    config.pop("hostname", None)
    config.pop("computer_name", None)

    ConfigManager.save_config(config)


def authenticate_user_in_ad(domain, username, password):
    ldap_user = f"{username}@{domain}"
    ldap_conn = domain_joiner_ldap.LDAP(domain, ldap_user, password)

    try:
        if not username or not password:
            print(_("no username or password"))
            return None

        ldap_conn.authenticate()

    except ldap.INVALID_CREDENTIALS:
        print(_("Invalid credentials."))
        return None
    except ldap.SERVER_DOWN:
        print(_("Server is not reachable."))
        return None
    except ldap.LDAPError as err:
        print(_("LDAP Error:"), err)
        return None
    except Exception as e:
        print(_("LDAP Authenticate Exception:"), e)
        return None
    else:
        return ldap_conn


def check_hostname_in_ad(domain, hostname, username, password):
    ldap_conn = authenticate_user_in_ad(domain, username, password)
    if ldap_conn is None:
        return False

    try:
        print(_("Checking if hostname {} exists in AD...").format(hostname))
        exists = ldap_conn.check_computer_exists_in_ad(hostname)
        print("Hostname exists in AD:", exists)

        if exists:
            print(_("Your computer still exists in Active Directory."))
    except ldap.LDAPError as err:
        print(_("Other LDAPError:"), err)
        sys.exit(1)
    except Exception as e:
        print(_("LDAP Authenticate Exception:"), e)
        sys.exit(1)
    finally:
        try:
            ldap_conn._unbind_connection()
        except Exception:
            pass


def join_domain(
    hostname, domain, user, password, ouaddress, connection_type, workgroup
):
    is_winbind = True if connection_type == "winbind" else False
    if is_winbind and workgroup is None:
        workgroup = domain_operations.get_netbios_name(domain)
        print("Workgroup: ", workgroup)

    if hostname is None:
        hostname = os.uname()[1]

    result = domain_operations.join(
        hostname,
        domain,
        user,
        password,
        ouaddress=ouaddress,
        realmd=connection_type == "sssd",
        winbind=connection_type == "winbind",
        workgroup=workgroup,
    )

    if result:
        for category, pattern in error_patterns.items():
            for key, message in pattern.items():
                if key in result:
                    print(message)

    ouaddress = ouaddress or ""

    model = Model()
    model.domain = domain
    model.username = user
    model.hostname = os.uname()[1]
    model.connection_type = connection_type
    model.organizational_unit = ouaddress
    save_config(model)


def leave_domain(username, password):
    config = read_config()
    connection_type = config.connection_type
    domain = config.domain
    hostname = config.hostname

    is_winbind = connection_type == "winbind"

    ldap_auth = authenticate_user_in_ad(domain, username, password)
    if ldap_auth is None:
        print(_("Authentication failed. Cannot leave the domain"))
        sys.exit(1)

    domain_operations.leave(
        user=username,
        password=password,
        winbind=is_winbind,
        realmd=(not is_winbind),
    )
    check_hostname_in_ad(domain, hostname, username, password)
    print(_("Successfully left the domain. Please restart your computer."))


def status():
    joined_domain_name = domain_operations.list(realmd=True)
    if joined_domain_name:
        print(_("joined={}").format(joined_domain_name))
        exit(0)

    joined_domain_name = domain_operations.list(winbind=True)
    if joined_domain_name:
        print(_("joined={}").format(joined_domain_name))
        exit(0)


def change_hostname(hostname):
    domain_operations.config_manager.set_hostname(hostname)


def main():
    parser = argparse.ArgumentParser(
        description=_("CLI application for Pardus Domain Joiner. You must run it with sudo."),
        add_help=False
    )

    parser.add_argument(
        "-h", "--help",
        action="help",
        help=_("show this help message and exit")
    )

    subparser = parser.add_subparsers(dest="command", required=True)

    # version
    subparser.add_parser("version", help=_("Show version"))

    # join
    join_parser = subparser.add_parser("join", help=_("Join a machine to the domain"))
    join_parser.add_argument("service", choices=["sssd", "winbind"])
    join_parser.add_argument("domain", help=_("Domain name"))
    join_parser.add_argument("user", help=_("Username"))
    join_parser.add_argument("-p", "--password", help=_("User password"))
    join_parser.add_argument("--ou", help=_("Organizational unit"))
    join_parser.add_argument("--workgroup")
    join_parser.add_argument("--hostname")

    # leave
    leave_parser = subparser.add_parser("leave", help=_("Leave the domain"))
    leave_parser.add_argument("user", help=_("Username"))
    leave_parser.add_argument("-p", "--password", help=_("User password"))

    # status
    subparser.add_parser("status", help=_("Check domain status"))

    # info
    info_parser = subparser.add_parser("info", help=_("Show discovered domain name"))
    info_parser.add_argument("domain", help=_("Domain name"))

    # change
    change_parser = subparser.add_parser("change", help=_("Change the hostname"))
    change_parser.add_argument("hostname", help=_("Hostname"))

    args = parser.parse_args()
    model = read_config()

    if hasattr(args, "password") and not args.password:
        args.password = getpass.getpass(_("Password for {}: ").format(args.user))

    if args.command == "join":
        status()
        join_domain(
            hostname=getattr(args, "hostname", None),
            domain=args.domain,
            user=args.user,
            password=args.password,
            ouaddress=getattr(args, "ou", None),
            connection_type=args.service,
            workgroup=getattr(args, "workgroup", None),
        )
    elif args.command == "leave":
        joined_domain_name = domain_operations.list(realmd=True) or domain_operations.list(winbind=True)
        if not joined_domain_name:
            print(_("This machine has not joined the domain before."))
            exit(1)
        leave_domain(username=args.user, password=args.password)
    elif args.command == "status":
        status()
    elif args.command == "info":
        discover_domain = domain_operations.discover_domain(args.domain)
        if discover_domain:
            print(_("Domain discovered:\n"), discover_domain)
        else:
            print(_("Server not found: {}").format(args.domain))
    elif args.command == "version":
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "__version__")
        default_version = "1.0.8"

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                version = f.readline().strip()
            print(_("Version: {}").format(version))
        else:
            print(_("Version: {}").format(default_version))
    elif args.command == "change":
        change_hostname(hostname=args.hostname)


if __name__ == "__main__":
    main()
