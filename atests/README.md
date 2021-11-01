# Development
All test cases are based on [Harvester Test Cases](https://harvesterhci.io/tests/)

## Background Knowledge

### Robot Framework
It is highly recommend to go through the [Robot Framework User Guide](https://robotframework.org/robotframework/4.1.2/RobotFrameworkUserGuide.html), to make sure you have the basic concept of Robot Framework execution environment.

[BuiltIn Library](https://robotframework.org/robotframework/latest/libraries/BuiltIn.html) is the base of keywords we will use for flow control and assertion.  [Robot Framework documentation](https://robotframework.org/robotframework/) also provide standard libraries for convenient.

### SeleniumLibrary
As our acceptance tests is testing the dashboard, [SeleniumLibrary](https://robotframework.org/SeleniumLibrary/SeleniumLibrary.html) is the major library we are deeply rely on.  It is recommend to get familiar with **CSS Selector** or **XPath**, if you already familiar with **CSS Selector**, here is the [cheat sheet of XPath](https://devhints.io/xpath).

### Other Libraries
In some case, you probably need another libraries to interact with OS, [login_utils.py](./resource/login_utils.py) should be the example for you to convert function into keywords, [Creating test libraries](https://robotframework.org/robotframework/4.1.2/RobotFrameworkUserGuide.html#id841) in User Guide would be more useful if you need more complex cases.

## Caveats

### Test Steps in Test Cases
It is highly recommend to use [Behavior-driven style](https://robotframework.org/robotframework/4.1.2/RobotFrameworkUserGuide.html#behavior-driven-style) for test steps, so that test report able to represent our expected result clearly.  For further explanation, you can check [the document](https://en.wikipedia.org/wiki/Acceptance_testing?oldformat=true#User_acceptance_testing) and relevant links in Robot Framework User Guide.

### Suite Keywords or Resource Keywords
Basically, put new keywords inside suite, unless there already have some keywords could be reused inside another suites.  But please notice that, when you moving some keywords out of suite, you must run those suites and pass tests to make sure you didn't break anything.

### Execute Javascript in SeleniumLibrary
Keyword _**Scripts Src in Head should Starts With**_ of [01__ui-source.robot](./04__Settings/01__ui-source.robot) would be a example for you to use **Execute Javascript** Keyword.  Additional notice is, script fragment provided will be executed as the body of _an anonymous function_, so you don't need create another function for it.
