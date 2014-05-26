#!/usr/bin/env python
#
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Manage collection and storing of active ip-addresses statistics"""

import logging
import time
from IPy import IP

import nav.activeipcollector.collector as collector
from nav.metrics.carbon import send_metrics
from nav.metrics.templates import metric_path_for_prefix

LOG = logging.getLogger('ipcollector.manager')
DATABASE_CATEGORY = 'activeip'


def run(days=None):
    """Fetch and store active ip"""
    return store(collector.collect(days))


def store(data):
    """Store data in rrd-files and update rrd-database

    :param data: a cursor.fetchall object containing all database rows we
    are to store

    """
    for db_tuple in data:
        store_tuple(db_tuple)

    LOG.info('Sent %s updates' % (len(data)))


def store_tuple(db_tuple):
    """Sends data to whisper with correct metric path

    :param db_tuple: a row from a rrd_fetchall object

    """
    prefix, when, ip_count, mac_count = db_tuple
    ip_range = find_range(prefix)

    metrics = [
        (metric_path_for_prefix(prefix, 'ip_count'), (when, ip_count)),
        (metric_path_for_prefix(prefix, 'mac_count'), (when, mac_count)),
        (metric_path_for_prefix(prefix, 'ip_range'), (when, ip_range))
    ]
    LOG.debug(metrics)
    send_metrics(metrics)


def find_range(prefix):
    """
    Find the max number of ip-addresses that are available for hosts
    on this prefix
    """
    try:
        ip = IP(prefix)
        if ip.version() == 4 and ip.len() > 2:
            return ip.len() - 2
        return 0
    except ValueError:
        return 0


def get_timestamp(timestamp=None):
    """Find timestamp closest to 30 minutes intervals"""

    def get_epoch():
        """Find epoch from a datetime object"""
        return int(time.mktime(timestamp.timetuple()))

    halfhour = 60 * 30
    epoch = get_epoch() if timestamp else int(time.time())
    difference = epoch % halfhour
    if difference > halfhour / 2:
        epoch += (halfhour - difference)
    else:
        epoch -= difference

    return epoch
