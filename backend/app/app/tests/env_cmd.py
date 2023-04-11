from dotenv import load_dotenv
from app.core.config import PROJECT_ROOT


def pytest_addoption(parser):
    parser.addoption(
        "--env", action="store", default="test",
        help="suffix of env file '.env.{suffix}', located in project root"
    )


def pytest_configure(config):
    """Hook function to set up environment variables after command line args passed"""
    # Set up your environment variables here
    print("Starting session here now")
    env_value = config.getoption("--env")
    # env_file = find_file(f"env.{env_value}")
    env_file = PROJECT_ROOT / f".env.{env_value}"
    assert load_dotenv(env_file)


# def find_file(name) -> Path | None:
#     dir_path = Path('.').resolve()
#     while dir_path:
#         env_file = dir_path / name
#         if env_file.is_file():
#             return env_file
#         dir_path = dir_path.parent
#     return None
