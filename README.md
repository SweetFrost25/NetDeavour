<p align="center"><img src="https://github.com/user-attachments/assets/40965716-558c-4ab9-b8c6-2cb5dbf3e7c8" width="120px" /></p>
<h1 align="center">NetDeavour</h1>
<p align="center">
<a href="https://pypi.org/project/scandeavour/"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/scandeavour"></a>
</p>
<p align="center">
Dashboard for merging, visualising and filtering network scans with multi-user support.
</p>

## 🔨 Installation

![Works on](https://img.shields.io/badge/Works%20on-Windows-green?style=flat)
![Works on](https://img.shields.io/badge/Works%20on-Linux-green?style=flat)
![Requires](https://img.shields.io/badge/Requires-Python%203.12+-green?style=flat)

```
pipx install netdeavour
```

## ✨ Features

- **Multi-user support** - Each user has their own isolated database
- **User authentication** - Secure login system with admin panel
- Load Nmap, Nessus and Masscan results (parsers are modular and can be added as plugins)
- View scans, hosts and open ports in an interactive graph with details for every node
- View all merged hosts in a dashboard
- Expand on host details (i.e. related scans, open ports, script outputs)
- Apply tags to hosts for custom prioritisation
- Chain modular drop-down filters to select relevant hosts based on their address, tag, open ports, script outputs, scans, OS, etc.
- Copy identified hosts and open ports to clipboard for a new scan
- Export hosts, ports and services to a CSV (e.g. for import in Word)
- Offline mode - once installed, no internet connection is required (a browser is required to access the dashboard though)

The following scanner outputs are supported. The main focus of this project lies on `nmap` but ingestors for other scanners can be integrated easily. Check out the [existing ingestors here](https://github.com/SweetFrost25/NetDeavour/tree/main/src/netdeavour/ingestors) if you want to extend one or build your own.

|Tool|Source|Scan information| Open ports | Service detection | Script output |
|---|---|:---:|:---:|:---:|:---:|
|Nmap|`nmap -oX <output>` |✔|✔|✔|✔|
|Nessus|Nessus export|limited|✔|✔|✔|
|Masscan|`masscan -oX <output>` |⛔|✔|⛔|⛔|
|Masscan|`masscan \| tee <output>` |⛔|✔|⛔|⛔|


## 📖 Usage

To visualize your scan results, simply start
```
netdeavour my_project.db
```
This will create a new project database (SQLITE) in the current folder. It will be used to store all your merged scans. The command will also start a Flask webserver running on a local port, exposing the web GUI.

### First Run

On first run, an admin user is automatically created:
- **Username:** `sweet`
- **Password:** `frost`

You can use this account to log in and create additional users through the admin panel.

### User Management

- **Regular users** can log in and work with their own isolated database
- **Administrators** can manage users through the account page:
  - Create new users
  - Block/unblock users
  - Delete users

> [!WARNING]  
> Do not run the dashboard with administrative capabilities and do not expose the GUI externally. While special inputs are treated with caution, malicious scan results were not considered during development. The dashboard now includes user authentication, but should still be used only in trusted networks.

## Development and contribution

You can clone the repository, switch to the `src` directory and create a virtual Python environment. Subsequently you can install the required libraries with `pip`. Check the `pyproject.toml` for the recommended Python and library versions.

```
cd src
python3 -m venv ./venv
source venv/bin/activate
pip3 install -e .
```

Or install dependencies manually:
```
pip3 install dash dash[diskcache] dash-bootstrap-components dash_ag_grid dash_cytoscape werkzeug
```

Lastly, start the application with
```
python3 -m netdeavour my_project.db [-d] # -d activates debug mode with hot reloading
```

You are welcome to open merge requests if you add features that you would like to see in the next version.

## 📃 License and attribution

Code released under the [MIT License](LICENSE).

Built using [Dash](https://github.com/plotly/dash/tree/dev) (licensed under MIT), [Dash Bootstrap Components](https://github.com/facultyai/dash-bootstrap-components) (licensed under Apache 2.0), and [Bootswatch](https://github.com/thomaspark/bootswatch) (licensed under MIT).
