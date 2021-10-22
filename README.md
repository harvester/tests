# ui-tests
Harvester UI testing based on RobotFramework.

## Running Test

### Prerequisite
It is highly recommdned to use virtual environment like `venv` to make a isolated environment, then install dependencies via pip:

```bash
pip install -r requirements.txt
```

After that, we still need **webdrivers** for Selenium.  In here, just use the tool [webdrivermanager](https://github.com/rasjani/webdrivermanager):

```bash
webdrivermanager chrome firefox
```
To notice that you have to install relevant browser for its webdriver. The tool also support other browsers like _Edge_ and _Opera_.

### Setup And Execute
To simply setup the environment information for test cases, you just need to copy `config.py.example` into `config.py` and update those variables inside:
```bash
cp config.py.example config.py
vim config.py
# or other editors that you familiar with
```
Then just execute:
```bash
robot -A arguments.txt atests
```

## Folder Structure
- `logs/` - default destination for log files
- `arguments.txt` - default command line options for test execution
- `config.py.example` - global variables for test suites
- `atest/` - acceptance test cases
    - `./resources` - robot framework resource files
    - `./<Num>__<TestName>` - relevant test cases