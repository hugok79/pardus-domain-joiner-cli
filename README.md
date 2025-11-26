# Pardus Domain Joiner CLI

[🇹🇷](./README_TR.md) | [🇬🇧](./README.md)

**Pardus Domain Joiner CLI** is a command-line tool for joining a domain, leaving a domain, checking domain status, viewing domain info, and changing the hostname on Pardus systems.

The CLI uses a custom-built library included in the project to handle domain-related tasks.

---

## Commands

```
pardus-domain-joiner-cli <command> [options]
```

### 1. Join

Join a domain using either the `sssd` or `winbind` service.

**Parameters:**

* `service`: `sssd` or `winbind` (which service to use)
* `domain`: Domain name (required)
* `user`: Username (required)
* `-p --password`: Password (optional, if not provided, the program will ask)
* `--ou`: Organizational Unit (optional)
* `--workgroup`: Workgroup name (optional, only for winbind)
* `--hostname`: Computer name (optional, if not provided, the current hostname is used)

**Example Usage:**

```bash
sudo pardus-domain-joiner-cli join sssd example.com admin
```

The program will prompt for a password.

---

### 2. Leave

Leave a joined domain.

**Parameters:**

* `user`: Username (required)
* `-p --password`: Password (optional, program will ask if not provided)

**Example Usage:**

```bash
sudo pardus-domain-joiner-cli leave admin
```

The program will prompt for a password.

---

### 3. Status

Check the connection status of the domain.

**Example Usage:**

```bash
sudo pardus-domain-joiner-cli status
```

---

### 4. Info

Displays discovery information for the specified domain.

**Parameters:**

* `domain`: Domain name (required)

**Example Usage:**

```bash
sudo pardus-domain-joiner-cli info example.com
```

---

### 5. Change

Change the hostname of the computer.

**Parameters:**

* `hostname`: New hostname (required)

**Example Usage:**

```bash
sudo pardus-domain-joiner-cli change newhostname
```

---

### 6. Version

Display the version of the CLI.

**Example Usage:**

```bash
pardus-domain-joiner-cli version
```

---

## Important Notes

* If the password is not provided in the command line, the program will ask securely at runtime.
* Commands must be run with `root` privileges.
* The `workgroup` parameter is only used with the `winbind` service.

---