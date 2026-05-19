import asyncio
from dotenv import load_dotenv
import sys
import os

from src.core import app_context
from src.core.logger.logger import LogCreator
from src.application import Application

def env_check():
    """
    环境检查
    - 检查环境变量
    """
    result = True

    logger.info("start env check")
    require_evns: list[str] = app_context.app_config.system.require_env
    for env_name in require_evns:
        env_value = os.getenv(env_name)
        if not env_value:
            result = False
            logger.warning(f"[{env_name}] === FAIL")
            continue
        logger.info(f"[{env_name}] === PASS")
    return result

def main():
    event_loop = asyncio.get_event_loop()
    app_context.event_loop = event_loop
    if not env_check():
        sys.exit("Environment check failed. Please check the environment variables.")

    try:
        main_app = Application(event_loop)
        main_app.initialize()
        logger.info("start event loop")
        event_loop.run_forever()
    except KeyboardInterrupt:
        logger.info("keyboard interrupt detected, exiting...")
        event_loop.run_until_complete(main_app.exit())
        sys.exit(0)
    except Exception as e:
        sys.exit(f"running exception: {e}")
load_dotenv()


LogCreator.instance.load_config(app_context.app_config.logging.model_dump())

logger = LogCreator.instance.create(__name__)

if __name__ == '__main__':
    main()
    
