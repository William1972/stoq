# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Listing and importing applications """

import gettext

from kiwi.component import implements
from stoqlib.lib.interfaces import IApplicationDescriptions

_ = gettext.gettext

# FIXME: Find a better description for apps. I just put here the
#        english translation/adaptation of the brazilian portuguese
#        translation on launchpad. hackedbellini 05-06-2011
_APPLICATIONS = {
    'admin' : (_("Administrative"),
               _("Application for system administration "
                 "and configuration."),
               'stoq-admin-app'),
    'financial' : (_("Financial"),
                   _("Application for financial management."),
                   'stoq-payable-app'),
    'inventory' : (_("Inventory"),
                   _("Application for stock auditing and adjustment."),
                   'stoq-inventory-app'),
    'payable' : (_("Accounts Payable"),
                 _("Application for management of payments to pay."),
                 'stoq-payable-app'),
    'pos' : (_("Point of Sales"),
             _("Application for selling products/services and "
               "fiscal coupon emission."),
             'stoq-pos-app'),
    'production' : (_("Production"),
                    _("Application for management of the production process."),
                    'stoq-production-app'),
    'purchase' : (_("Purchase"),
                  _("Application for management of purchases "
                  "and product/service registration"),
                    'stoq-purchase-app'),
    'receivable' : (_("Accounts Receivable"),
                    _("Application for management of payments to receive."),
                    'stoq-bills'),
    'sales' : (_("Sales"),
               _("Application for quotes management and creation "
                 "and commission calculation."),
               'stoq-sales-app'),
    'stock' : (_("Stock"),
               _("Application for stock management."),
               'stoq-stock-app'),
    'till' : (_("Till"),
              _("Application for till management."),
              'stoq-till-app'),
}

def get_application_names():
    """Get a list of application names, useful for launcher programs

    @returns: application names
    """
    return _APPLICATIONS.keys()


class ApplicationDescriptions:

    implements(IApplicationDescriptions)

    def get_application_names(self):
        return get_application_names()

    def get_descriptions(self):
        app_desc = []
        for name, (label, description, icon) in _APPLICATIONS.items():
            app_desc.append((name, label, icon, description))
        return app_desc


class Application(object):
    """
    Describes an application

    @ivar name: short name of application
    @ivar fullname: complete name of application
    @ivar icon: application icon
    @ivar description: long description of application
    """

    def __init__ (self, name, fullname, icon, description):
        self.name = name
        self.fullname = fullname
        self.icon = icon
        self.description = description
