import os

from crewai_tools import EXASearchTool, FileReadTool
from dotenv import load_dotenv

load_dotenv()

# TOOL 1: FileReadTool
log_reader_tool = FileReadTool()

# TOOL 2: EXASearchTool
os.environ["EXA_API_KEY"] = os.getenv("EXA_API_KEY")

exa_search_tool = EXASearchTool()
