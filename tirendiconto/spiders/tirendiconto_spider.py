# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import re

import scrapy


REPORT_XPATH = '//div[@class="pubblicazione"]/table//a/@href'
REPORT_URL = 'rendicontazione.php?user={_id}&tipo={_type}&mese={month}'
HREF_REGEX = r"javascript:Popup\('rendicontazione\.php\?mese=-1&user=(?P<_id>\d+)&tipo=(?P<_type>[DS])'\)"


class TiRendiContoSpider(scrapy.Spider):

    name = 'tirendiconto'
    allowed_domains = ['tirendiconto.it']
    start_urls = ['https://www.tirendiconto.it/trasparenza/']

    def parse(self, response):
        for href in response.xpath(REPORT_XPATH).extract():
            match = re.search(HREF_REGEX, href)
            if match:
                _id = match.group('_id')
                _type = match.group('_type')
                for month in range(4, 6):
                    yield self._build_request(response, _id, _type, month, self.parse_old_report)
                for month in range(6, 13):
                    yield self._build_request(response, _id, _type, month, self.parse_mid_report)
                for month in range(13, 61):
                    yield self._build_request(response, _id, _type, month, self.parse_new_report)

    def parse_old_report(self, response):
        _id = response.xpath('//input[@id="utente"]/@value').extract_first()
        _type = response.xpath('//input[@id="tipoUtente"]/@value').extract_first()
        month = response.xpath('//input[@id="mese"]/@value').extract_first()

        name = response.xpath('//table[1]/tr[1]/td[2]/text()').extract_first()
        claimed_expenses = self._convert_to_cents(response.xpath('//table[2]/tr[1]/td[2]/text()').extract_first())
        wire_transfer = self._convert_to_cents(response.xpath('//table[4]/tr[1]/td[2]/text()').extract_first())
        expenses = self._convert_to_cents(response.xpath('//table[7]/tr[9]/td[2]/text()').extract_first())
        mandate_expenses = self._convert_to_cents(response.xpath('//table[8]/tr[4]/td[2]/text()').extract_first())

        yield {
            'id': _id,
            'type': _type,
            'month': month,
            'name': name,
            'wire_transfer': wire_transfer,
            'claimed_expenses': claimed_expenses,
            'total_expenses': self._add(
                expenses,
                mandate_expenses,
            ),
        }

    def parse_mid_report(self, response):
        _id = response.xpath('//input[@id="utente"]/@value').extract_first()
        _type = response.xpath('//input[@id="tipoUtente"]/@value').extract_first()
        month = response.xpath('//input[@id="mese"]/@value').extract_first()

        name = response.xpath('//table[1]/tr[1]/td[2]/text()').extract_first()
        wire_transfer = self._convert_to_cents(response.xpath('//table[2]/tr[1]/td[2]/text()').extract_first())
        claimed_expenses = self._convert_to_cents(response.xpath('//table[4]/tr[3]/td[2]/text()').extract_first())
        expenses = self._convert_to_cents(response.xpath('//table[6]/tr[9]/td[2]/text()').extract_first())
        other_expenses = self._convert_to_cents(response.xpath('//table[7]/tr[8]/td[2]/text()').extract_first())
        mandate_expenses = self._convert_to_cents(response.xpath('//table[8]/tr[10]/td[2]/text()').extract_first())

        yield {
            'id': _id,
            'type': _type,
            'month': month,
            'name': name,
            'wire_transfer': wire_transfer,
            'claimed_expenses': claimed_expenses,
            'total_expenses': self._add(
                expenses,
                other_expenses,
                mandate_expenses,
            ),
        }

    def parse_new_report(self, response):
        _id = response.xpath('//input[@id="utente"]/@value').extract_first()
        _type = response.xpath('//input[@id="tipoUtente"]/@value').extract_first()
        month = response.xpath('//input[@id="mese"]/@value').extract_first()

        name = response.xpath('//table[1]/tr[1]/td[2]/text()').extract_first()
        wire_transfer = self._convert_to_cents(response.xpath('//table[2]/tr[1]/td[2]/text()').extract_first())
        claimed_expenses = self._convert_to_cents(response.xpath('//table[4]/tr[4]/td[2]/text()').extract_first())
        home_expenses = self._convert_to_cents(response.xpath('(//div/table)[1]/tr[1]/td[2]/text()').extract_first())
        other_expenses = self._convert_to_cents(response.xpath('(//div/table)[1]/tr[3]/td[2]/text()').extract_first())
        phone_expenses = self._convert_to_cents(response.xpath('(//div/table)[1]/tr[5]/td[2]/text()').extract_first())
        travel_expenses = self._convert_to_cents(response.xpath('(//div/table)[1]/tr[7]/td[2]/text()').extract_first())
        eating_expenses = self._convert_to_cents(response.xpath('(//div/table)[1]/tr[9]/td[2]/text()').extract_first())
        events_expenses = self._convert_to_cents(response.xpath('(//div/table)[2]/tr[1]/td[2]/text()').extract_first())
        collaborators_expenses = self._convert_to_cents(response.xpath('(//div/table)[2]/tr[3]/td[2]/text()').extract_first())
        consulents_expenses = self._convert_to_cents(response.xpath('(//div/table)[2]/tr[5]/td[2]/text()').extract_first())
        office_expenses = self._convert_to_cents(response.xpath('(//div/table)[2]/tr[7]/td[2]/text()').extract_first())

        yield {
            'id': _id,
            'type': _type,
            'month': month,
            'name': name,
            'wire_transfer': wire_transfer,
            'claimed_expenses': claimed_expenses,
            'total_expenses': self._add(
                home_expenses, other_expenses, phone_expenses,
                travel_expenses, eating_expenses, events_expenses,
                collaborators_expenses, consulents_expenses, office_expenses),
        }

    def _add(self, *args):
        if all(arg is None for arg in args):
            return None

        return sum(arg for arg in args if arg is not None)

    def _build_absolute_url(self, response, _id, _type, month):
        relative_url = REPORT_URL.format(_id=_id, _type=_type, month=month)
        absolute_url = response.urljoin(relative_url)

        return absolute_url

    def _build_request(self, response, _id, _type, month, callback):
        absolute_url = self._build_absolute_url(
            response, _id, _type, month)

        return scrapy.Request(absolute_url, callback=callback)

    def _convert_to_cents(self, amount):
        try:
            return int(amount.split()[0].replace('.', '').replace(',', ''))
        except AttributeError:
            return None
