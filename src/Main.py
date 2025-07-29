import argparse
import getpass
import os
import logging

from pardus_domain_joiner import domain_operations
from pardus_domain_joiner import config_manager
from pardus_domain_joiner import domain_joiner_realmd
from pardus_domain_joiner import domain_joiner_winbind


class SSSDService:
    def join(self, comp_name, domain, user, password, ou, workgroup=None):
        domain_operations.join(comp_name, domain, user, password, ou, realmd=True)

    def leave(self, user, password):
        domain_operations.leave(realmd=True, user=user, password=password)

    def status(self):
        return domain_operations.list(realmd=True)

    def discover(self, domain):
        domain_joiner_realmd.discover(domain)


class WinbindService:
    def join(self, comp_name, domain, username, password, ou, workgroup):
        domain_operations.join(comp_name, domain, username, password, ou, workgroup, winbind=True)

    def leave(self, user, password):
        domain_operations.leave(winbind=True, user=user, password=password)

    def status(self):
        return domain_operations.list(winbind=True)

    def discover(self):
        domain_joiner_winbind.discover()


class DomainManager:
    def __init__(self, strategy):
        self.strategy = strategy

    def join(self, comp_name, domain, user, password, ou=None, workgroup=None):
        print("The join process has been initiated.")
        self.strategy.join(comp_name, domain, user, password, ou, workgroup)
        print("The join process is completed")

    def leave(self, user, password):
        print("The leave process has been initiated.")
        self.strategy.leave(user, password)
        print("The leave process is completed")

    def status(self):
        realm = self.strategy.status()
        print("Querying domain name information...")
        if realm:
            print("Domain Name: ", realm)
            print("You are in the domain.")
        else:
            print("Domain information not found.")
            print("You are not in the domain.")

    def discover(self, domain):
        self.strategy.discover(domain)


def change_hostname(comp_name):
    print("Hostname is being changed.")
    config_manager.set_hostname(comp_name)


def get_manager(service):
    if service == "sssd":
        return SSSDService()
    elif service == "winbind":
        return WinbindService()
    else:
        raise ValueError("Unknown service")


def main():
    parser = argparse.ArgumentParser(description="CLI application for Pardus Domain Joiner. You must run it with sudo.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logs")

    subparser = parser.add_subparsers(dest="command", required=True)

    # join
    join_parser = subparser.add_parser("join", help="Join the domain")
    join_parser.add_argument("service", choices=["sssd", "winbind"])
    join_parser.add_argument("-d", "--domain", required=True)
    join_parser.add_argument("-u", "--user", required=True)
    join_parser.add_argument("-p", "--password")
    join_parser.add_argument("-c", "--computer")
    join_parser.add_argument("--ou")
    join_parser.add_argument("--workgroup")

    # leave
    leave_parser = subparser.add_parser("leave", help="Leave the domain")
    leave_parser.add_argument("service", choices=["sssd", "winbind"])
    leave_parser.add_argument("-u", "--user", required=True)
    leave_parser.add_argument("-p", "--password")

    # status
    status_parser = subparser.add_parser("status", help="Check domain status")
    status_parser.add_argument("service", choices=["sssd", "winbind"])

    # info
    info_parser = subparser.add_parser("info", help="Show discovered domain name")
    info_parser.add_argument("-d", "--domain", required=True)

    # change hostname
    change_parser = subparser.add_parser("change", help="Change the hostname")
    change_parser.add_argument("-c", "--computer", required=True)

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    if hasattr(args, "password") and not args.password:
        args.password = getpass.getpass(f"Password for {args.user}: ")

    if args.command in ["join", "leave", "status"]:
        manager = get_manager(args.service)
        domain_manager = DomainManager(manager)

    if args.command == "join":
        comp_name = args.computer or os.uname()[1]
        domain_manager.join(
            comp_name=comp_name,
            domain=args.domain,
            user=args.user,
            password=args.password,
            ou=getattr(args, "ou", None),
            workgroup=getattr(args, "workgroup", None)
        )
    elif args.command == "leave":
        domain_manager.leave(user=args.user, password=args.password)
    elif args.command == "status":
        domain_manager.status()
    elif args.command == "info":
        print(domain_operations.discover_domain(args.domain))
    elif args.command == "change":
        change_hostname(comp_name=args.computer)


if __name__ == "__main__":
    main()
