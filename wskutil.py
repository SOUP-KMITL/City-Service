***REMOVED***
***REMOVED***

***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***


def createPackage(pname):
***REMOVED***
***REMOVED***

***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***

        httpCode = resp.status_code
***REMOVED***

***REMOVED***
        print("createPackage: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("createPackage: connection to external service timeout")
***REMOVED***
***REMOVED***
        if httpCode != 200:
***REMOVED***
***REMOVED***
            print("createPackage: " + error)
    ***REMOVED*** Exception(httpCode, error)
    finally:
        return httpCode


def deletePackage(pname):
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***

        httpCode = resp.status_code
***REMOVED***

***REMOVED***
        print("deletePackage: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("deletePackage: connection to external service timeout")
***REMOVED***
***REMOVED***
        if httpCode != 200:
***REMOVED***
***REMOVED***
            print("deletePackage: " + error)
    ***REMOVED*** Exception(httpCode, error)
    finally:
        return httpCode


def updateAction(action, kind, code, overwrite):
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***

***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***

        httpCode = resp.status_code
***REMOVED***

***REMOVED***
        print("updateAction: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("updateAction: connection to external service timeout")
***REMOVED***
***REMOVED***
        if httpCode != 200:
***REMOVED***
***REMOVED***
            print("updateAction: " + error)
    ***REMOVED*** Exception(httpCode, error)
    finally:
        return httpCode


def deleteAction(action):
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***

        httpCode = resp.status_code
***REMOVED***

***REMOVED***
        print("deleteAction: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("deleteAction: connection to external service timeout")
***REMOVED***
***REMOVED***
        if httpCode != 200:
***REMOVED***
***REMOVED***
            print("deleteAction: " + error)
    ***REMOVED*** Exception(httpCode, error)
    finally:
        return httpCode


def invokeAction(action, params):
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***

        httpCode = resp.status_code
***REMOVED***

***REMOVED***
        print("invokeAction: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("invokeAction: connection to external service timeout")
***REMOVED***
***REMOVED***
        if httpCode != 200:
***REMOVED***
***REMOVED***
            print("invokeAction: " + error)
    ***REMOVED*** Exception(httpCode, error)
    finally:
        return httpCode, result
