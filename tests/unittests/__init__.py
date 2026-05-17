# Re-export every test module so `python -m unittest tests.unittests` picks them
# all up. Without these imports, that command would treat this package as a single
# module and find zero tests (since the test classes only live in the submodules).
# Add a new line here whenever you add a new test_*.py file to this folder.
from .test_app import *  
from .test_events import *  
from .test_friends import *  
from .test_groups import *  
from .test_ical import * 
from .test_reglog import *  
from .test_user import * 
