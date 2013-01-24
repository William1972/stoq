# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Search dialogs for fiscal objects """

import datetime

import gtk
from kiwi.currency import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.objectlist import SearchColumn
from storm.expr import Join

from stoqlib.api import api
from stoqlib.database.viewable import DeprecatedViewable
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.person import Branch
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import Sale
from stoqlib.domain.station import BranchStation
from stoqlib.domain.till import Till
from stoqlib.gui.base.search import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class TillFiscalOperationsView(DeprecatedViewable):
    """Stores informations about till payment tables

    :attribute date:         the date when the entry was created
    :attribute description:  the entry description
    :attribute value:        the entry value
    :attribute station_name: the value of name branch_station name column
    """

    columns = dict(
        id=Payment.id,
        identifier=Payment.identifier,
        date=Payment.open_date,
        description=Payment.description,
        value=Payment.value,
        cfop=CfopData.code,
        station_name=BranchStation.name,
        branch_id=Branch.id,
        status=Till.status,
        )

    joins = [
        Join(Till,
                    Till.id == Payment.till_id),
        Join(BranchStation,
                    BranchStation.id == Till.station_id),
        Join(Branch,
                    Branch.id == BranchStation.branch_id),
        Join(PaymentGroup,
                    PaymentGroup.id == Payment.group_id),
        Join(Sale,
                    Sale.group_id == PaymentGroup.id),
        Join(CfopData,
                    CfopData.id == Sale.cfop_id),
        ]


class TillFiscalOperationsSearch(SearchDialog):
    title = _(u"Till Fiscal Operations")
    table = TillFiscalOperationsView
    size = (750, 500)
    searching_by_date = True
    searchbar_labels = _(u"matching:"),
    searchbar_result_strings = _(u"fiscal operation"), _(u"fiscal operations")

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description'])
        self.executer.add_query_callback(self._get_query)

        # Status
        items = [(v, k) for k, v in Till.statuses.items()
                    if k != Till.STATUS_PENDING]
        items.insert(0, (_(u'Any'), None))
        status_filter = ComboSearchFilter(_(u'Show entries of type'), items)
        status_filter.select(Till.STATUS_OPEN)
        self.add_filter(status_filter,
                        position=SearchFilterPosition.TOP,
                        columns=['status'])

    def get_columns(self, *args):
        return [SearchColumn('identifier', title=_('#'), width=60,
                             justify=gtk.JUSTIFY_RIGHT, format="%05d",
                             data_type=int, sorted=True),
                SearchColumn('date', title=_('Date'), width=100,
                             data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('description', title=_('Description'),
                             data_type=str, expand=True),
                SearchColumn('station_name', title=_('Station'), data_type=str,
                             width=120),
                SearchColumn('cfop', title=_('C.F.O.P.'), data_type=str,
                             width=100, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('value', _('Value'), data_type=currency,
                             width=80)]

    #
    # Private
    #

    def _get_query(self, state):
        branch = api.get_current_branch(self.store)
        return self.search_table.branch_id == branch.id
