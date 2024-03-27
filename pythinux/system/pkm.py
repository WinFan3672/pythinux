import os
import shutil
import configparser
import urllib.request
import traceback

disallowInstalld = getTerm() == "installd"

if not disallowInstalld:
    installd = load_program("installd", currentUser, libMode=True)
libsemver = load_program("libsemver", currentUser, libMode=True)
shell = load_program("shell", currentUser, libMode=True)

global config, version

config = configparser.ConfigParser()
config.add_section("repos")
config.set("repos", "core", "https://codeberg.org/Pythinux/Core/raw/branch/main/db.ini")

applications = configparser.ConfigParser()
# config.set("repos", "community", "https://codeberg.org/Pythinux/Community/raw/branch/main/db.ini")

version = [4, 0, 0]

def downloadFile(url, fileName):
    """
    Download a remote HTTP resource and save it to a file.
    """
    urllib.request.urlretrieve(url, file.evalDir(fileName, currentUser))

def sectionToDict(config, section):
    """
    Convert a ConfigParser section to a dictionary.
    
    Args:
    - config: ConfigParser object
    - section: Name of the section
    
    Returns:
    - dict containing the key-value pairs of the section
    """
    dict_section = {}
    options = config.options(section)
    for option in options:
        dict_section[option] = config.get(section, option)
    return dict_section

def getPackageData(offline=True, silent=False):
    """
    This function returns package data as a dict
    """
    repos = sectionToDict(config, "repos")
    packageData = configparser.ConfigParser()
    if offline:
        packageData.read(file.evalDir("config/pkmdata.ini", currentUser))
    else:
        if not silent:
            print("Updating database...")
        for repo in repos:
            if not silent:
                print("Downloading '{}'...".format(repo))
            downloadFile(repos[repo], "/tmp/repo")
            packageData.read("tmp/repo")
    with open(file.evalDir("/config/pkmdata.ini", currentUser), "w") as f:
        packageData.write(f)
    if not silent and not offline:
        print("Successfully updated database.")
    return packageData

def getPackageList():
    return os.listdir(file.evalDir("/share/pkm/programs/", currentUser))

def saveConfig():
    with open(file.evalDir("/config/pkm.ini", currentUser), "w") as f:
        config.write(f)

def loadConfig():
    config.read(file.evalDir("/config/pkm.ini", currentUser))

def installPackage(package, yesMode=False, depMode=False):
    clearTemp(currentUser)
    data = getPackageData()
    url = data.get(package, "url", fallback=None)
    if url:
        downloadFile(url, "tmp/program.szip4")
        result = installd.installd("tmp/program.szip4", yesMode)
        if result == 1:
            print("ERROR: User action canceled.")
        elif result == 0:
            if depMode:
                print("Successfully installed '{}'.".format(package))
        elif result == 2:
            print("ERROR: Package '{}' is already installed.".format(package))
            print("ERROR: To rectify this, run 'pkm remove {}' and try again.".format(package))
        else:
            print("ERROR: Exit code {}".format(result))

def removePackage(package):
    ini = configparser.ConfigParser()
    ini.read(file.evalDir("/share/pkm/programs/{}".format(package), currentUser))
    if ini.has_section("Files"):
        files = dict([x for x in ini.items("Files") if "@" not in x[1]])
    else:
        files = []
    if ini.has_option("Folders", "folders"):
        folders = [file.evalDir(x, currentUser) for x in ini.get("Folders", "folders").split("; ")]
        ignored = ini.get("Folders", "ignored").split("; ")
    else:
        folders = []
    for x in files:
        fn = file.evalDir(x, currentUser)
        if os.path.isfile(fn):
            os.remove(fn)
    
    for folder in [x for x in folders if x not in ignored]:
        shutil.rmtree(folder)

    os.remove(file.evalDir("/share/pkm/programs/{}".format(package), currentUser))
    print("Successfully removed program.")

def main(args):
    loadConfig()
    saveConfig()
    if args == ["update"]:
        getPackageData(False)
    elif args in [["version"], ["ver"], ["v"]]:
        div()
        print("PKM {}".format(".".join([str(x) for x in version])))
        div()
        print("PKM (c) Pythinux team 2022-2024, some rights reserved.")
        div()
    elif args == ["repo"]:
        div()
        print("pkm repo [arg]")
        div()
        print("Manage repositories.")
        div()
        print("Positional arguments:")
        print("    add <name> <url>: add a repository")
        print("    list: lists all repositories")
        print("    rm <name>: remove a repository")
        div()
    elif args in [["repo", "list"], ["repo", "ls"]]:
        repos = sectionToDict(config, "repos")
        div()
        for repo in repos:
            print("{} --> {}".format(repo, repos[repo]))
        div()
    elif args == ["repo", "add"]:
        div()
        print("pkm repo add <name> <url")
        div()
        print("Adds a repository to PKM's database.")
        div()
    elif "repo" in args and "add" in args and len(args) == 4:
        args.remove("repo")
        args.remove("add")
        name = args[0]
        url = args[1]
        loadConfig()
        config.set("repos", name, url)
        saveConfig()
        getPackageData(False)
    elif args == ["all"]:
        packages = getPackageData(False, True)
        for package in packages.sections():
            div()
            print("{} {}".format(package, packages.get(package, "version")))
            print("    {}".format(packages.get(package, "name")))
            print("    {}".format(packages.get(package, "description")))
        div()
        if len(packages.sections()) == 0:
            print("ERROR: No packages found.")
            div()
    elif args == ["repo", "rm"]:
        div()
        print("pkm repo rm <name>")
        div()
        print("Remove a repository from PKM's repo list.")
        div()
    elif "repo" in args and "rm" in args and len(args) == 3:
        args.remove("repo")
        args.remove("rm")
        name = args[0]
        loadConfig()
        config.remove_option("repos", name)
        saveConfig()
        print("Successfully removed repository '{}'.".format(name))
    elif args == ["allc"]:
        packages = getPackageData(False, True)
        print("\n".join(packages.sections()))
    elif args == ["install"]:
        div()
        print("pkm install <package(s)> [-y]")
        div()
        print("Downloads a package file and installs it.")
        div()
    elif "install" in args:
        args.remove("install") ## Apparently it removes the FIRST instance, not all of them
        if "-y" in args:
            yesMode = True
            args.remove("-y")
        else:
            yesMode = False
        if "-d" in args:
            depMode = True
            yesMode = True
            args.remove("-d")
        else:
            depMode = False
        for arg in args:
            installPackage(arg, yesMode, depMode)
    elif args == ["list"]:
        ls = sorted(getPackageList())
        div()
        if ls:
            print("\n".join(ls))
        else:
            print("ERROR: No packages installed.")
        div()
    elif args == ["remove"]:
        div()
        print("pkm remove <package>")
        div()
        print("Remove a package.")
        div()
    elif "remove" in args and len(args) == 2:
        args.remove("remove")
        removePackage(args[0])
    elif args == ["clear", "-y"]:
        for program in getPackageList():
            removePackage(program)
    elif args == ["clear"]:
        print("ERROR: This will remove ALL of your packages.")
        print("ERROR: Run `pkm clear -y` to confirm.")
    else:
        div()
        print("pkm [args]")
        div()
        print("Pythinux package manager.")
        div()
        print("Positional arguments:")
        print("    install <package>: installs a package")
        # print("    search <package name>: searches for a package by name")
        print("    remove <package>: remove a package")
        print("    clear: removes all installed packages")
        print("    update: updates the database")
        # print("    upgrade: upgrades all installed packages")
        print("    list: lists all installed programs")
        # print("    info <package>: prints information about an installed package")
        # print("    rinfo <package>: prints information about an installable package")
        print("    all: lists all installable packages")
        print("    allc: lists all installable packages [compact]")
        print("    repo: manages repositories")
        # print("    batch <database>: installs every package in a particular database")
        # print("    from <database> <package>: installs a package from a specific database")
        print("    version: states the version of PKM")
        div()
