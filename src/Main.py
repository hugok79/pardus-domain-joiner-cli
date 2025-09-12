import argparse
import getpass
import os
import logging
import sys

import ldap
import managers.ConfigManager as ConfigManager
from pardus_domain_joiner import domain_operations
from pardus_domain_joiner import domain_joiner_ldap


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


def authenticate_user_in_ad(domain, hostname, username, password):
    ldap_user = f"{username}@{domain}"
    ldap_check = domain_joiner_ldap.LDAP(domain, ldap_user, password)

    try:
        ldap_check.authenticate()
        print("Authenticating the user on LDAP...")

        is_hostname_in_ad = ldap_check.check_computer_exists_in_ad(hostname)
        print("is hostname exists in AD:", is_hostname_in_ad)

        if is_hostname_in_ad:
            print("You have successfully left the domain. But your computer still exists in Active Directory.")

        ldap_check._unbind_connection()

    except ldap.INVALID_CREDENTIALS:
        print("Invalid credentials.")
        ldap_check._unbind_connection()
        return
    except ldap.SERVER_DOWN:
        print("Server is not reachable.")
        ldap_check._unbind_connection()
        return
    except ldap.LDAPError as err:
        print("Other LDAPError:", err)
        ldap_check._unbind_connection()
        return
    except Exception as e:
        print("LDAP Authenticate Exception:", e)
        ldap_check._unbind_connection()
        return

def join_domain(
    hostname, domain, user, password, ouaddress, connection_type, workgroup
):
    is_winbind = True if connection_type == "winbind" else False
    if is_winbind:
        workgroup = domain_operations.get_netbios_name(domain)
        print("workgroup", workgroup)

    domain_operations.join(
        hostname,
        domain,
        user,
        password,
        ouaddress=ouaddress,
        realmd=connection_type == "sssd",
        winbind=connection_type == "winbind",
        workgroup=workgroup,
    )

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

    is_winbind = True if connection_type == "winbind" else False

    domain_operations.leave(
        user=username,
        password=password,
        winbind=is_winbind,
        realmd=(not is_winbind),
    )
    authenticate_user_in_ad(domain, hostname, username, password)


def status():
    joined_domain_name = domain_operations.list(realmd=True)
    if joined_domain_name:
        print(f"joined={joined_domain_name}")
        exit(0)

    joined_domain_name = domain_operations.list(winbind=True)
    if joined_domain_name:
        print(f"joined={joined_domain_name}")
        exit(0)


def change_hostname(hostname):
    domain_operations.config_manager.set_hostname(hostname)


def main():
    parser = argparse.ArgumentParser(
        description="CLI application for Pardus Domain Joiner. You must run it with sudo."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logs"
    )

    subparser = parser.add_subparsers(dest="command", required=True)

    # join
    join_parser = subparser.add_parser("join", help="Join the domain")
    join_parser.add_argument("service", choices=["sssd", "winbind"])
    join_parser.add_argument("domain", help="Domain name")
    join_parser.add_argument("user", help="Username")
    join_parser.add_argument("-p", "--password")
    join_parser.add_argument("--ou")
    join_parser.add_argument("--workgroup")

    # leave
    leave_parser = subparser.add_parser("leave", help="Leave the domain")
    leave_parser.add_argument("user", help="Username")
    leave_parser.add_argument("-p", "--password")

    # status
    subparser.add_parser("status", help="Check domain status")

    # info
    info_parser = subparser.add_parser("info", help="Show discovered domain name")
    info_parser.add_argument("domain", help="Domain name")

    # change hostname
    change_parser = subparser.add_parser("change", help="Change the hostname")
    change_parser.add_argument("computer", help="Hostname")

    args = parser.parse_args()
    model = read_config()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    if hasattr(args, "password") and not args.password:
        args.password = getpass.getpass(f"Password for {args.user}: ")

    if args.command == "join":
        status()
        join_domain(
            hostname=os.uname()[1],
            domain=args.domain,
            user=args.user,
            password=args.password,
            ouaddress=getattr(args, "ou", None),
            connection_type=args.service,
            workgroup=getattr(args, "workgroup", None),
        )
    elif args.command == "leave":
        leave_domain(username=args.user, password=args.password)
        print("You need to restart your computer")
    elif args.command == "status":
        status()
    elif args.command == "info":
        discover_domain = domain_operations.discover_domain(args.domain)
        if discover_domain:
            print("Domain discovered:\n", discover_domain)
        else:
            print(f"Server not found: {args.domain}")
    elif args.command == "change":
        change_hostname(hostname=args.computer)


if __name__ == "__main__":
    main()
