import argparse
import getpass
import os
import logging
import sys

from pardus_domain_joiner import domain_operations
from pardus_domain_joiner import config_manager
from pardus_domain_joiner import domain_joiner_realmd
from pardus_domain_joiner import domain_joiner_winbind
import toml

CONFIG_DIR = "/usr/share/pardus/pardus-domain-cli/config"
CONFIG_FILE = "pdj_cli_config.toml"
USER_PROFILE_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)

os.makedirs(CONFIG_DIR, exist_ok=True)

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

        if workgroup is None:
            workgroup = domain_operations.get_netbios_name(domain)

        domain_operations.join(comp_name, domain, username, password, ou, workgroup, winbind=True)

    def leave(self, user, password):
        domain_operations.leave(winbind=True, user=user, password=password)

    def status(self):
        return domain_operations.list(winbind=True)

    def discover(self):
        domain_joiner_winbind.discover()


class DomainManager:
    def __init__(self, strategy=None, domain=None, hostname=None):
        if strategy:
            self.strategy = strategy
            service_name = strategy.__class__.__name__
            self.save_service(name = service_name,
                              domain = domain,
                              hostname = hostname)
        elif self.load_service():
            saved_service = self.load_service().get('name')
            if not saved_service:
                print("No service selected because the system has not joined a domain before. Please run 'join --service ...' first.")
                sys.exit(1)
            self.strategy = self.create_strategy(saved_service)
        else:
            self.strategy = strategy
            if not self.strategy:
                print("No service selected because the system has not joined a domain before. Please run 'join --service ...' first.")
                sys.exit(1)
            service_name = strategy.__class__.__name__
            self.save_service(name = service_name,
                              domain = domain,
                              hostname = hostname)

        self.domain_status = self.status()

    def save_service(self, name, domain, hostname):
        config = {
            'service': {
                'name': name,
                'domain': domain,
                'hostname': hostname
            }
        }
        with open(USER_PROFILE_PATH, 'w') as f:
            toml.dump(config, f)

    def load_service(self):
        if not os.path.exists(USER_PROFILE_PATH):
            return None
        with open(USER_PROFILE_PATH, 'r') as f:
            config = toml.load(f)
        service = config.get('service', {})
        return {
            'name': service.get('name'),
            'domain': service.get('domain'),
            'hostname': service.get('hostname')
        }

    def create_strategy(self, name):
        if name == "SSSDService":
            return SSSDService()
        elif name == "WinbindService":
            return WinbindService()
        else:
            raise ValueError(f"Unknown service: {name}")

    def join(self, comp_name, domain, user, password, ou=None, workgroup=None):
        if not self.domain_status:
            print("The join process has been initiated.")
            self.strategy.join(comp_name, domain, user, password, ou, workgroup)
            print("The join process is completed")

    def leave(self, user, password):
        if self.domain_status:
            print("The leave process has been initiated.")
            self.strategy.leave(user, password)
            if self.load_service():
                domain = self.load_service().get('domain')
                hostname = self.load_service().get('hostname')
                check_ad = domain_operations.check_hostname_in_ad(domain, hostname, user, password)
                if not check_ad:
                    print("The user could not be deleted from AD. Delete it via AD.")
            print("The leave process is completed")

    def status(self):
        realm = self.strategy.status()
        print("Querying domain name information...")
        if realm:
            print("Domain Name: ", realm)
            print("You are in the domain.")
            return True
        else:
            print("Domain information not found.")
            print("You are not in the domain.")
            return False

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
    change_parser.add_argument("computer", help="Computer name")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    if hasattr(args, "password") and not args.password:
        args.password = getpass.getpass(f"Password for {args.user}: ")

    if args.command == "join":
        manager = get_manager(args.service)
        domain_manager = DomainManager(manager, args.domain, os.uname()[1])
        domain_manager.join(
            comp_name=os.uname()[1],
            domain=args.domain,
            user=args.user,
            password=args.password,
            ou=getattr(args, "ou", None),
            workgroup=getattr(args, "workgroup", None)
        )
    elif args.command == "leave":
        domain_manager = DomainManager()
        domain_manager.leave(user=args.user, password=args.password)
    elif args.command == "status":
        domain_manager = DomainManager()
    elif args.command == "info":
        discover_domain = domain_operations.discover_domain(args.domain)
        if discover_domain:
            print("Domain discovered:\n",
                  discover_domain)
        else:
            print(f"Server not found: {args.domain}")
    elif args.command == "change":
        change_hostname(comp_name=args.computer)


if __name__ == "__main__":
    main()
