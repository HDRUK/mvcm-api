import unittest

# Your TestApp class should be imported or defined here

class CustomTestResult(unittest.TestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_info = []

    def addSuccess(self, test):
        json_data = getattr(test, "json_response", None)
        self.test_info.append({"test": str(test), "status": "success", "json_response": json_data})

    def addError(self, test, err):
        json_data = getattr(test, "json_response", None)
        self.test_info.append({"test": str(test), "status": "error", "message": str(err), "json_response": json_data})

    def addFailure(self, test, err):
        json_data = getattr(test, "json_response", None)
        self.test_info.append({"test": str(test), "status": "failure", "message": str(err), "json_response": json_data})

class CustomTestRunner(unittest.TextTestRunner):
    resultclass = CustomTestResult

    def run(self, test):
        result = super().run(test)
        return {
            "total_tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "successful": result.wasSuccessful(),
            "detailed": result.test_info
        }