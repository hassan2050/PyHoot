## @package PyHoot.base
# Base module
## @file base.py Implementation of @ref PyHoot.base


import logging


class Base(object):
    """Base of all objects"""

    ## Log prefix to use.
    LOG_PREFIX = 'my'

    @property
    def logger(self):
        """Logger."""
        return self._logger

    def __init__(self):
        """Constructor."""
        self._logger = logging.getLogger(
            '%s.%s' % (
                self.LOG_PREFIX,
                self.__module__,
            ),
        )


def setup_logging(stream=None, level=logging.INFO):
    """Setup logging system.
    @returns (logger) program logger.
    """
    logger = logging.getLogger(Base.LOG_PREFIX)
    logger.propagate = False
    logger.setLevel(level)

    try:
        h = logging.StreamHandler(stream)
        #h.setLevel(logging.DEBUG)
        h.setLevel(level)
        h.setFormatter(
            logging.Formatter(
                fmt=(
                    '%(asctime)-14s '
                    '[%(levelname)-5s] '
                    '%(name)s::%(funcName)s:%(lineno)d '
                    '%(message)s'
                ),
                datefmt="%m/%d %H:%M:%S",
            ),
        )
        logger.addHandler(h)
    except IOError:
        logging.warning('Cannot initialize logging', exc_info=True)

    return logger
