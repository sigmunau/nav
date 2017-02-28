#
# Copyright (C) 2009-2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Machine tracker forms"""
from datetime import date, timedelta

from django import forms

from nav.macaddress import MacPrefix
from nav.web.machinetracker import iprange


class MachineTrackerForm(forms.Form):
    """General fields for forms in machinetracker"""
    dns = forms.BooleanField(required=False, initial=False,
                             help_text="Show dns (if any)")
    days = forms.IntegerField(initial=7, required=False,
                              widget=forms.TextInput(attrs={'size': 3}),
                              help_text="Days back in time to search")
    start = forms.DateTimeField(required=False, help_text="Start date of query")
    end = forms.DateTimeField(required=False, help_text="End date of query")
    time_mode_choices = [
        ("machinetracker-filter-days", "Last days"),
        ("machinetracker-filter-active", "Only Active"),
        ("machinetracker-filter-custom", "Custom"),
    ]
    time_mode = forms.ChoiceField(choices=time_mode_choices,
                                  initial="machinetracker-filter-days")

    def __init__(self, *args, **kwargs):
        super(MachineTrackerForm, self).__init__(*args, **kwargs)
        self.fields['start'].widget.attrs['class'] = 'datepicker'
        self.fields['end'].widget.attrs['class'] = 'datepicker'

    def clean_days(self):
        """Clean the days fields"""
        data = int(self.cleaned_data['days'])
        if data < 0:
            raise forms.ValidationError("I can't see into the future. "
                                        "Please enter a positive number.")

        try:
            date.today() - timedelta(days=data)
        except OverflowError:
            raise forms.ValidationError(
                "They didn't have computers %s days ago" % data)

        return data

    def clean(self):
        data = self.cleaned_data.copy()
        if data['time_mode'] == 'machinetracker-filter-days':
            if not data['days']:
                raise forms.ValidationError(
                    'Days must be given if time mode is Last Days')
            data['start'] = date.today() - timedelta(days=data['days'])
            data['end'] = date.today()
            data['time_mode'] = 'machinetracker-filter-custom'
        if data['time_mode'] == 'machinetracker-filter-custom':
            if not data['start'] or not data['end']:
                raise forms.ValidationError(
                    'Both start and end must be given')
        return data


class IpTrackerForm(MachineTrackerForm):
    """Form for searching by IP-address"""
    choices = [('active', 'Active'), ('inactive', 'Inactive'),
               ('both', 'Both')]

    ip_range = forms.CharField(widget=forms.TextInput(
        attrs={'placeholder': 'IP-address or range'}))
    period_filter = forms.ChoiceField(widget=forms.RadioSelect(),
                                      choices=choices,
                                      initial='active')
    netbios = forms.BooleanField(required=False, initial=False,
                                 help_text="Show netbios name (if any)")

    source = forms.BooleanField(required=False, initial=False,
                                help_text="Show which router the data is retrieved from")

    def clean_ip_range(self):
        """Clean the ip_range field"""
        data = self.cleaned_data['ip_range']
        try:
            data = iprange.MachinetrackerIPRange.from_string(data)
        except ValueError as error:
            raise forms.ValidationError("Invalid syntax: %s" % error)
        return data


class MacTrackerForm(MachineTrackerForm):
    """Form for searching by MAC-address"""
    mac = forms.CharField(widget=forms.TextInput(
        attrs={'placeholder': 'Mac-address'}))
    netbios = forms.BooleanField(required=False, initial=False,
                                 help_text="Netbios name (if any)")

    def clean_mac(self):
        """Clean the mac field"""
        try:
            mac = MacPrefix(self.cleaned_data['mac'])
        except ValueError as error:
            raise forms.ValidationError(error)
        return mac


class SwitchTrackerForm(forms.Form):
    """Form for searching by switch fields"""
    switch = forms.CharField()
    module = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'size': 3}))
    port = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'size': 16}))
    days = forms.IntegerField(
        initial=7,
        widget=forms.TextInput(attrs={'size': 3}))


class NetbiosTrackerForm(MachineTrackerForm):
    """Form for searching by netbios name"""
    search = forms.CharField(widget=forms.TextInput(
        attrs={'placeholder': 'Netbios name'}))

    def clean_search(self):
        """Make sure blank spaces and such is removed from search"""
        return self.cleaned_data['search'].strip()
