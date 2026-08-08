import ib_async
from pprint import PrettyPrinter, pformat
from pydantic import BaseModel
from datetime import datetime
import inspect

pp = PrettyPrinter(indent=4)
for name, object in inspect.getmembers(ib_async, inspect.isclass):
    print(f"Class: {name}")
    print(f"Object: {object}")
    print(f"Object type: {type(object)}")
    print(f"Object attributes: {dir(object)}")
    print(f"Object dict: {object.__dict__}")
    print(f"Object help: {help(object)}")
    print(f"Object pretty print: {pp.pprint(object)}")
