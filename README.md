# X4FProjector

A command-line tool that reads X4 Foundations game files (.cat and .dat files),
extracts raw stats about various game objects and outputs the data into files
that are easy for humans or other programs and scripts to read.

The purpose is to provide as much (useful) information as possible to aid
players who want to optimize their play, to provide this information in format
that is easy to read and process, and to provide this information on demand
(no need to wait for wiki pages to update their data for a new version of the
game -- just rerun this script).

Beware that a lot of data that is outputted is very raw and requires additional
processing to obtain something usable. Also, some of the outputted data might
not be available in game (yet).

Features:
  * **Supported game objects and stats**:
    * Engines and thrusters - thrust, boost, travel, hull, and more.
    * Shields - capacity, recharge, hull, and more.
    * Ships - class, hull, drag, inertia, num. weapons, num. engines, num.
shields, num. turrets, cargobay, docks, ship storage, and more.
    * Lasers and missile launchers - damage, reload time, heat, hull, bullet
stats, missile stats, and more.
    * Wares - price, production methods, tags, volume, license, module
construction, blueprints, and more.
    * *TODO Station modules*.
  * **Supported output formats**:
    * CSV. Data is saved in a tabular format which can be loaded into Excel.
Some things are omitted.
    * JSON. Data is saved in a structured format. Nothing is omitted.
    * YAML (requires pyyaml). Data is saved in a structured format. Nothing is
omitted.
  * **Multiple language support**. Can resolve strings such as ship names to
any language that the game supports.
  * **Fast**. Needs less than 6 seconds to produce all the output files on my
system with an SSD.
  * **Easy to use**.
  * **Lazy .cat file loader**. Loads game files effortlessly so you don't need
to perform any extra steps. Avoids loading all the .cat files unless it has to.
  * **File system loader**. Reads game data from extracted .cat files.
  * **Reusable code**. Feel free to pick up parts of this project such as the
CatFileLoader, LanguageResolver or the MacroDB for your project. I would
appreciate if you would credit my work if you use parts of my project.
  * *TODO Support for mods*.

## Installation

Prerequisites:
* [Python 3](https://www.python.org/). Tested on 3.7.
* [Python lxml](https://lxml.de/). Used for parsing XML files.
* Optional: [PyYAML](https://pyyaml.org/). Used for YAML output.

After you got the prerequisites installed you can download the [latest project
archive](https://github.com/bno1/X4FProjector/releases) and extract it on your
disk or clone this repository on your computer by running:
```bash
git clone https://github.com/bno1/X4FProjector.git
```

### Installing the prerequisites on Windows

1. Install the latest release of Python 3.7 from the
[offical site](https://www.python.org/downloads/). Make sure to enable `pip`
and `Add Python to environment variables`.
2. Open a cmd terminal and enter: ```pip install lxml pyyaml```.

### Installing the prerequisites on Linux

Almost all Linux distributions should come with Python 3 included. Python lxml
and pyyaml can be installed using your package manager or by installing
`python3-pip` and running `# pip3 install lxml pyyaml`.

## Usage

On Windows: open a terminal in the directory of this project (Shift+right click
in the directory, select `Open command window here` or `Open PowerShell window
here`). Run:
```bash
python.exe ./X4FProjector.py --help
```

On Linux: open a terminal in the directory of this project and run one of:
```bash
./X4FProjector.py --help
# or
python3 ./X4FProjector.py --help
```

Common command-line options:
* `-h, --help`. Show help message.
* `-v, --verbose`. Enable more verbose output.
- `--file-loader FILE_LOADER`. File loader to use. Accepted values: `fs` and
`cat`, defaulting to `cat` if this option is not specified. See the **More
details** section for more information.
- `-g GAME_ROOT, --game-root GAME_ROOT`. Path to the game installation.
Default: the current directory. This option will be passed to the file loader:
  * When using the Cat file loader this option must point to the directory
where the game .cat files are placed.
  * When using the File system loader this option must point to the directory
where the game files are extracted. The directory should contain the directories
assets and libraries.
- `-l LANGUAGE, --lang LANGUAGE`. Language to use for resolving game strings.
If this option is not specified then the English language will be used. See the
**More details** section for more information.

Common commands:
* **export**: reads raw game data and exports it to one or more files.

Export command-line options:
* `-d EXPORT_DIR, --dir EXPORT_DIR`. Directory to export game data to. Defaults
to the current directory if not specified.
* `-f EXPORT_FORMAT, --format EXPORT_FORMAT`. Format to export data as.
Defaults to CSV if not specified. Supported values:
  * **csv**. Creates tabular .csv files that can be loaded in Excel.
  * **json**. Creates structured .json files.
  * **yaml**. Creates structured .yaml files.
* `all`. Export all game data that this script can read.
* `engines`. Export engine and thruster data. Will create a `engines.{csv,json,
yaml}` file in the export directory.
* `missilelaunchers`. Export missile launcher weapon and turret data. Will
create a `missilelaunchers.{csv,json,yaml}` file in the export directory.
* `shields`. Export shield data. Will create a `shields.{csv,json,yaml}` file
in the export directory.
* `ships`. Export ship data. Will create a `ship.{csv,json,yaml}` file in the
export directory.
* `wares`. Export ware data. Will create a `ware.{csv,json,yaml}` file in the
export directory.
* `weapons`. Export laser weapon and turret data. Will create a `weapons.{csv,
json,yaml}` file in the export directory.

Extra commands that most users don't need:
* **resolve-string**: read a game string template from the command line and
tries to resolve it using the game language files. String templates contain
placeholders of the form `{page_id, text_id}` that reference language-dependent
strings.

### Exporting game data

To export all the game data that this script reads into the directory `x4_data`
in the CSV format simply run:
```
./X4FProjector.py -g path/to/x4 export all -d ./x4_data -f csv
```
This will override existing files in `x4_data`.

The `all` is optional if no other object is specified. The following has the
same effect:
```
./X4FProjector.py -g path/to/x4 export -d ./x4_data -f csv
```

You can choose which game objects to export:
```
./X4FProjector.py -g path/to/x4 export ships engines wares -d ./x4_data -f csv
```

To change the language used to resolve strings pass an `-l` option. Example for
German:
```
./X4FProjector.py -g path/to/x4 -l de export ships engines wares -d ./x4_data -f csv
```

### resolve-string example
```
./X4FProjector.py -g path/to/x4 resolve-string 'This ship is {20101,30302}' 'That ship is {20101,30303}'
This ship is Nemesis Vanguard
That ship is Nemesis Sentinel
```

### resolve-string example using German language
```
./X4FProjector.py -g path/to/x4 -l de resolve-string 'This ship is {20101,30302}' 'That ship is {20101,30303}'
This ship is Nemesis Angreifer
That ship is Nemesis Verteidiger
```

## More details

### Cat file loader

Loads .cat and .dat files directory from the game installation. It looks for
files named 01.cat 01.dat, 02.cat 02.dat, ... 99.cat 99.dat and stops when a
file cannot be found.

Files with a higher numerical value have a higher priority. E.g. if both 01.cat
and 05.cat contain
`assets/props/Engines/macros/engine_arg_s_travel_01_mk1_macro.xml` then
X4Projector will load the one from 05.dat instead of 01.cat.

Beware that if you add your own .cat and .dat files to the game directory those
might be loaded too.

### File system loader

Loads game files from a location where .cat files have been extracted. This
loader is faster than the Cat file loader because it doesn't have to parse .cat
files (this takes about 1 second).

Game files can be extracted using
[X Catalog Tool](https://www.egosoft.com/download/x_rebirth/bonus_en.php?download=597) or another .cat extractor. When
extracting you have to:
* Extract each .cat file, from the lowest to the highest number such that
higher-numbered cat files override the content of lower-numbered ones.
* Check the `Keep folder hierarchy` box.

### Language support

The language used to resolve game strings is specified via `-l` or `--language`
option.

The argument to this option can be:
* 2-letter language code. E.g. en, fr, ru.
* 3-letter language code. E.g. eng, fra, fre, rus.
* Language name in English. E.g. english, french, russian.
* Language name in the language itself. E.g. english, français, русский.

For Chinese you can add the `-cn` or `-tw` suffix to choose between simplified
and traditional.

See the `LANG_TABLE` in `X4Projector.py` for a full list of accepted names.

## How can you contribute

I'm happy to look into and possibly accept any contribution to this project.

* Try to run this script on your computer for your game installation. Post an
issue if you have any problems.
* Report any inaccuracies that you find in the exported data.
* Report code bugs or documentation typos.
* Suggest new stats to export and why would they be useful.
* Suggest new features or show interest in ones already suggested. I will be
more likely to implement features that are highly demanded.
* Suggest improvement to the source code or documentation.
