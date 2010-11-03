#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# vim:syntax=python:sw=4:ts=4:expandtab

import os
import logging
import logging.config

def setup_logs(config):
    confdir = os.path.expanduser('~/vogelerclient')
    # See http://docs.python.org/library/logging.html#configuration-file-format
    logging.config.fileConfig(os.path.join(confdir,'logging.conf'))
    logger = logging.getLogger('vogeler-client')

'''
logger = logging.getLogger('vogeler-client')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
ch.setFormatter(formatter)

# Add ch to logger
logger.addHandler(ch)
'''

