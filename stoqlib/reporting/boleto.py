# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2011-2012 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

# This is mostly lifted from
# http://code.google.com/p/pyboleto licensed under MIT

import sys
import traceback

from reportlab.graphics.barcode.common import I2of5
from reportlab.lib import colors, pagesizes, utils
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from stoqlib.exceptions import ReportError
from stoqlib.lib.crashreport import collect_traceback
from stoqlib.lib.boleto import BoletoException, get_bank_info_by_number
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BoletoPDF(object):

    (FORMAT_BOLETO,
     FORMAT_CARNE) = range(2)

    def __init__(self, file_descr, format=FORMAT_BOLETO):
        self.file_descr = file_descr
        self.width = 190 * mm
        self.widthCanhoto = 70 * mm
        self.space = 2
        self.fontSizeTitle = 6
        self.fontSizeValue = 9

        pagesize = pagesizes.A4
        if format == self.FORMAT_CARNE:
            pagesize = pagesizes.landscape(pagesize)
            self.heightLine = 5.75 * mm
        else:
            self.heightLine = 6.5 * mm

        self.deltaTitle = self.heightLine - (self.fontSizeTitle + 1)
        self.deltaFont = self.fontSizeValue + 1
        self.format = format

        self.pdfCanvas = canvas.Canvas(self.file_descr, pagesize=pagesize)
        self.pdfCanvas.setStrokeColor(colors.black)

        self.boletos = []

    def drawReciboSacadoCanhoto(self, boletoDados, x, y):
        self.pdfCanvas.saveState()
        self.pdfCanvas.translate(x * mm, y * mm)

        linhaInicial = 12

        # Horizontal Lines
        self.pdfCanvas.setLineWidth(2)
        self._horizontalLine(0, 0, self.widthCanhoto)

        self.pdfCanvas.setLineWidth(1)
        self._horizontalLine(0, (linhaInicial + 0) * self.heightLine,
                             self.widthCanhoto)
        self._horizontalLine(0, (linhaInicial + 1) * self.heightLine,
                             self.widthCanhoto)

        self.pdfCanvas.setLineWidth(2)
        self._horizontalLine(0, (linhaInicial + 2) * self.heightLine,
                             self.widthCanhoto)

        # Vertical Lines
        self.pdfCanvas.setLineWidth(1)
        self._verticalLine(self.widthCanhoto - (35 * mm),
                           (linhaInicial + 0) * self.heightLine, self.heightLine)
        self._verticalLine(self.widthCanhoto - (35 * mm),
                           (linhaInicial + 1) * self.heightLine, self.heightLine)

        self.pdfCanvas.setFont('Helvetica-Bold', 6)
        self.pdfCanvas.drawRightString(self.widthCanhoto,
                                       0 * self.heightLine + 3,
                                       'Recibo do Sacado')

        # Titles
        self.pdfCanvas.setFont('Helvetica', 6)
        self.deltaTitle = self.heightLine - (6 + 1)

        self.pdfCanvas.drawString(
            self.space,
            (((linhaInicial + 0) * self.heightLine)) + self.deltaTitle,
            'Nosso N??mero')
        self.pdfCanvas.drawString(
            self.widthCanhoto - (35 * mm) + self.space,
            (((linhaInicial + 0) * self.heightLine)) + self.deltaTitle,
            'Vencimento')
        self.pdfCanvas.drawString(
            self.space,
            (((linhaInicial + 1) * self.heightLine)) + self.deltaTitle,
            'Ag??ncia/C??digo do Benefici??rio')
        self.pdfCanvas.drawString(
            self.widthCanhoto - (35 * mm) + self.space,
            (((linhaInicial + 1) * self.heightLine)) + self.deltaTitle,
            'Valor Documento')

        # Values
        self.pdfCanvas.setFont('Helvetica', 9)
        heighFont = 9 + 1

        valorDocumento = self._format_value(boletoDados.payment.value)

        self.pdfCanvas.drawString(
            self.space,
            (((linhaInicial + 0) * self.heightLine)) + self.space,
            boletoDados.format_nosso_numero())

        self.pdfCanvas.drawString(
            self.widthCanhoto - (35 * mm) + self.space,
            (((linhaInicial + 0) * self.heightLine)) + self.space,
            boletoDados.payment.due_date.strftime('%d/%m/%Y'))
        self.pdfCanvas.drawString(
            self.space,
            (((linhaInicial + 1) * self.heightLine)) + self.space,
            boletoDados.agencia_conta)
        self.pdfCanvas.drawString(
            self.widthCanhoto - (35 * mm) + self.space,
            (((linhaInicial + 1) * self.heightLine)) + self.space,
            valorDocumento)

        demonstrativo = boletoDados.demonstrativo[0:12]
        for i in range(len(demonstrativo)):
            parts = utils.simpleSplit(demonstrativo[i], 'Helvetica', 9,
                                      self.widthCanhoto)
            self.pdfCanvas.drawString(
                2 * self.space,
                (((linhaInicial - 1) * self.heightLine)) - (i * heighFont),
                parts[0])

        self.pdfCanvas.restoreState()

        return (self.widthCanhoto / mm,
                ((linhaInicial + 2) * self.heightLine) / mm)

    def drawReciboSacado(self, boletoDados, x, y):
        self.pdfCanvas.saveState()
        self.pdfCanvas.translate(x * mm, y * mm)

        linhaInicial = 16

        # Horizontal Lines
        self.pdfCanvas.setLineWidth(1)
        # Cedente
        self._horizontalLine(0,
                             linhaInicial * self.heightLine, self.width)
        # Endere??o
        self._horizontalLine(0,
                             (linhaInicial + 1) * self.heightLine, self.width)
        # Sacado
        self._horizontalLine(0,
                             (linhaInicial - 1) * self.heightLine, self.width)

        self.pdfCanvas.setLineWidth(2)
        self._horizontalLine(0,
                             (linhaInicial + 2) * self.heightLine, self.width)

        # Vertical Lines

        # Vertical line 1
        # Linha Sacado
        self.pdfCanvas.setLineWidth(1)
        self._verticalLine(
            self.width - (35 * mm) - (30 * mm) - (40 * mm),
            (linhaInicial - 1) * self.heightLine,
            1 * self.heightLine)
        # Linha Cedente
        self._verticalLine(
            self.width - (35 * mm) - (30 * mm) - (40 * mm),
            (linhaInicial + 1) * self.heightLine,
            1 * self.heightLine)

        # Vertical line 2
        # Cedente
        self.pdfCanvas.setLineWidth(1)
        self._verticalLine(
            self.width - (35 * mm) - (30 * mm),
            (linhaInicial + 1) * self.heightLine,
            1 * self.heightLine)
        # Sacado
        self.pdfCanvas.setLineWidth(1)
        self._verticalLine(
            self.width - (35 * mm) - (30 * mm),
            (linhaInicial - 1) * self.heightLine,
            1 * self.heightLine)

        # Vertical line 3
        # Cedente/Endere??o/Sacado
        self.pdfCanvas.setLineWidth(1)
        self._verticalLine(
            self.width - (35 * mm),
            (linhaInicial + -1) * self.heightLine,
            3 * self.heightLine)

        # Head
        self.pdfCanvas.setLineWidth(2)
        self._verticalLine(40 * mm,
                           (linhaInicial + 2) * self.heightLine, self.heightLine)
        self._verticalLine(60 * mm,
                           (linhaInicial + 2) * self.heightLine, self.heightLine)

        if boletoDados.logo_image_path:
            self.pdfCanvas.drawImage(
                boletoDados.logo_image_path,
                0, (linhaInicial + 2) * self.heightLine + 3,
                40 * mm,
                self.heightLine,
                preserveAspectRatio=True,
                anchor='sw')

        self.pdfCanvas.setFont('Helvetica-Bold', 18)
        self.pdfCanvas.drawCentredString(
            50 * mm,
            (linhaInicial + 2) * self.heightLine + 3,
            boletoDados.codigo_dv_banco)

        self.pdfCanvas.setFont('Helvetica-Bold', 10)
        self.pdfCanvas.drawRightString(
            self.width,
            (linhaInicial + 2) * self.heightLine + 3,
            'Recibo do Pagador')

        # Titles
        self.pdfCanvas.setFont('Helvetica', 6)
        self.deltaTitle = self.heightLine - (6 + 1)

        self.pdfCanvas.drawRightString(
            self.width,
            self.heightLine,
            'Autentica????o Mec??nica')

        # Linha Benefici??rio
        self.pdfCanvas.drawString(
            0,
            (((linhaInicial + 1) * self.heightLine)) + self.deltaTitle,
            'Benefici??rio')
        self.pdfCanvas.drawString(
            self.width - (35 * mm) - (30 * mm) - (40 * mm) + self.space,
            (((linhaInicial + 1) * self.heightLine)) + self.deltaTitle,
            'Ag??ncia/C??digo Benefici??rio')
        self.pdfCanvas.drawString(
            self.width - (35 * mm) - (30 * mm) + self.space,
            (((linhaInicial + 1) * self.heightLine)) + self.deltaTitle,
            'Data Documento')
        self.pdfCanvas.drawString(
            self.width - (35 * mm) + self.space,
            (((linhaInicial + 1) * self.heightLine)) + self.deltaTitle,
            'Vencimento')

        # Linha Endere??o
        self.pdfCanvas.drawString(
            0,
            (((linhaInicial + 0) * self.heightLine)) + self.deltaTitle,
            'Endere??o Benefici??rio')
        self.pdfCanvas.drawString(
            self.width - (35 * mm) + self.space,
            (((linhaInicial + 0) * self.heightLine)) + self.deltaTitle,
            'CNPJ Benefici??rio')

        # Linha Sacado
        self.pdfCanvas.drawString(
            0,
            (((linhaInicial - 1) * self.heightLine)) + self.deltaTitle,
            'Pagador')
        self.pdfCanvas.drawString(
            self.width - (35 * mm) - (30 * mm) - (40 * mm) + self.space,
            (((linhaInicial - 1) * self.heightLine)) + self.deltaTitle,
            'Nosso N??mero')
        self.pdfCanvas.drawString(
            self.width - (35 * mm) - (30 * mm) + self.space,
            (((linhaInicial - 1) * self.heightLine)) + self.deltaTitle,
            'N. do documento')
        self.pdfCanvas.drawString(
            self.width - (35 * mm) + self.space,
            (((linhaInicial - 1) * self.heightLine)) + self.deltaTitle,
            'Valor Documento')

        self.pdfCanvas.drawString(
            0,
            (((linhaInicial - 2) * self.heightLine)) + self.deltaTitle,
            'Demonstrativo')

        # Values
        self.pdfCanvas.setFont('Helvetica', 9)
        heighFont = 9 + 1

        # Valores da linha Benefici??rio
        self.pdfCanvas.drawString(
            0 + self.space,
            (((linhaInicial + 1) * self.heightLine)) + self.space,
            boletoDados.branch.get_description())
        self.pdfCanvas.drawString(
            self.width - (35 * mm) - (30 * mm) - (40 * mm) + self.space,
            (((linhaInicial + 1) * self.heightLine)) + self.space,
            boletoDados.agencia_conta)
        self.pdfCanvas.drawString(
            self.width - (35 * mm) - (30 * mm) + self.space,
            (((linhaInicial + 1) * self.heightLine)) + self.space,
            boletoDados.payment.open_date.strftime('%d/%m/%Y'))
        self.pdfCanvas.drawString(
            self.width - (35 * mm) + self.space,
            (((linhaInicial + 1) * self.heightLine)) + self.space,
            boletoDados.payment.due_date.strftime('%d/%m/%Y'))

        # Valores da linha Endere??o
        # Endere??o
        address = boletoDados.branch.person.get_main_address()
        self.pdfCanvas.drawString(
            0 + self.space,
            (((linhaInicial + 0) * self.heightLine)) + self.space,
            '{}, {}'.format(address.get_address_string(),
                            address.get_details_string()))
        # CNPJ
        self.pdfCanvas.drawString(
            self.width - (35 * mm) + self.space,
            (((linhaInicial + 0) * self.heightLine)) + self.space,
            boletoDados.branch.person.company.cnpj)

        # Valores da linha Sacado
        valorDocumento = self._format_value(boletoDados.payment.value)

        self.pdfCanvas.drawString(
            0 + self.space,
            (((linhaInicial - 1) * self.heightLine)) + self.space,
            boletoDados.payer.name[:80])
        self.pdfCanvas.drawString(
            self.width - (35 * mm) - (30 * mm) - (40 * mm) + self.space,
            (((linhaInicial - 1) * self.heightLine)) + self.space,
            boletoDados.format_nosso_numero())
        self.pdfCanvas.drawString(
            self.width - (35 * mm) - (30 * mm) + self.space,
            (((linhaInicial - 1) * self.heightLine)) + self.space,
            str(boletoDados.payment.identifier))
        self.pdfCanvas.drawString(
            self.width - (35 * mm) + self.space,
            (((linhaInicial - 1) * self.heightLine)) + self.space,
            valorDocumento)

        demonstrativo = boletoDados.demonstrativo[0:25]
        for i in range(len(demonstrativo)):
            self.pdfCanvas.drawString(
                2 * self.space,
                (((linhaInicial - 2) * self.heightLine)) - (i * heighFont),
                demonstrativo[i])

        self.pdfCanvas.restoreState()

        return (self.width / mm,
                ((linhaInicial + 2) * self.heightLine) / mm)

    def drawHorizontalCorteLine(self, x, y, width):
        self.pdfCanvas.saveState()
        self.pdfCanvas.translate(x * mm, y * mm)

        self.pdfCanvas.setLineWidth(1)
        self.pdfCanvas.setDash(1, 2)
        self._horizontalLine(0, 0, width * mm)

        self.pdfCanvas.restoreState()

    def drawVerticalCorteLine(self, x, y, height):
        self.pdfCanvas.saveState()
        self.pdfCanvas.translate(x * mm, y * mm)

        self.pdfCanvas.setLineWidth(1)
        self.pdfCanvas.setDash(1, 2)
        self._verticalLine(0, 0, height * mm)

        self.pdfCanvas.restoreState()

    def drawReciboCaixa(self, boletoDados, x, y):
        self.pdfCanvas.saveState()

        self.pdfCanvas.translate(x * mm, y * mm)

        # De baixo para cima posicao 0,0 esta no canto inferior esquerdo
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle)

        y = 1.5 * self.heightLine
        self.pdfCanvas.drawRightString(
            self.width,
            (1.5 * self.heightLine) + self.deltaTitle - 1,
            'Autentica????o Mec??nica / Ficha de Compensa????o')

        # Primeira linha depois do codigo de barra
        y += self.heightLine
        self.pdfCanvas.setLineWidth(2)
        self._horizontalLine(0, y, self.width)
        self.pdfCanvas.drawString(
            self.width - (45 * mm) + self.space,
            y + self.space, 'C??digo de baixa')
        self.pdfCanvas.drawString(0, y + self.space, 'Pagador / Avalista')

        y += self.heightLine
        self.pdfCanvas.drawString(0, y + self.deltaTitle, 'Pagador')

        # Linha grossa dividindo o Sacado
        y += self.heightLine
        self.pdfCanvas.setLineWidth(2)
        self._horizontalLine(0, y, self.width)

        address = boletoDados.payer.get_main_address()
        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue)
        self.pdfCanvas.drawString(15 * mm, (y - 10),
                                  boletoDados.payer.name[:80])
        self.pdfCanvas.drawString(15 * mm, (y - 10) - (1 * self.deltaFont),
                                  address.get_address_string()[:80])
        self.pdfCanvas.drawString(15 * mm, (y - 10) - (2 * self.deltaFont),
                                  address.get_details_string()[:80])

        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle)

        # Linha vertical limitando todos os campos da direita
        self.pdfCanvas.setLineWidth(1)
        self._verticalLine(self.width - (45 * mm), y, 9 * self.heightLine)
        self.pdfCanvas.drawString(
            self.width - (45 * mm) + self.space,
            y + self.deltaTitle,
            '(=) Valor cobrado')

        # Campos da direita
        y += self.heightLine
        self._horizontalLine(self.width - (45 * mm), y, 45 * mm)
        self.pdfCanvas.drawString(
            self.width - (45 * mm) + self.space,
            y + self.deltaTitle,
            '(+) Outros acr??scimos')

        y += self.heightLine
        self._horizontalLine(self.width - (45 * mm), y, 45 * mm)
        self.pdfCanvas.drawString(
            self.width - (45 * mm) + self.space,
            y + self.deltaTitle,
            '(+) Mora/Multa')

        y += self.heightLine
        self._horizontalLine(self.width - (45 * mm), y, 45 * mm)
        self.pdfCanvas.drawString(
            self.width - (45 * mm) + self.space,
            y + self.deltaTitle,
            '(-) Outras dedu????es')

        y += self.heightLine
        self._horizontalLine(self.width - (45 * mm), y, 45 * mm)
        self.pdfCanvas.drawString(
            self.width - (45 * mm) + self.space,
            y + self.deltaTitle,
            '(-) Descontos/Abatimentos')
        self.pdfCanvas.drawString(
            0,
            y + self.deltaTitle,
            'Instru????es')

        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue)
        instrucoes = boletoDados.instrucoes[:7]
        for i in range(len(instrucoes)):
            parts = utils.simpleSplit(instrucoes[i], 'Helvetica', 9,
                                      self.width - 45 * mm)
            if not parts:
                parts = [' ']
            self.pdfCanvas.drawString(
                2 * self.space,
                y - (i * self.deltaFont),
                parts[0])
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle)

        # Linha horizontal com primeiro campo Uso do Banco
        y += self.heightLine
        self._horizontalLine(0, y, self.width)
        self.pdfCanvas.drawString(0, y + self.deltaTitle, 'Uso do banco')

        self._verticalLine((30) * mm, y, 2 * self.heightLine)
        self.pdfCanvas.drawString(
            (30 * mm) + self.space,
            y + self.deltaTitle,
            'Carteira')

        self._verticalLine((30 + 20) * mm, y, self.heightLine)
        self.pdfCanvas.drawString(
            ((30 + 20) * mm) + self.space,
            y + self.deltaTitle,
            'Esp??cie')

        self._verticalLine(
            (30 + 20 + 20) * mm,
            y,
            2 * self.heightLine)
        self.pdfCanvas.drawString(
            ((30 + 40) * mm) + self.space,
            y + self.deltaTitle,
            'Quantidade')

        self._verticalLine(
            (30 + 20 + 20 + 20 + 20) * mm, y, 2 * self.heightLine)
        self.pdfCanvas.drawString(
            ((30 + 40 + 40) * mm) + self.space, y + self.deltaTitle, 'Valor')

        self.pdfCanvas.drawString(
            self.width - (45 * mm) + self.space,
            y + self.deltaTitle,
            '(=) Valor documento')

        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue)
        self.pdfCanvas.drawString(
            (30 * mm) + self.space,
            y + self.space,
            boletoDados.carteira)
        self.pdfCanvas.drawString(
            ((30 + 20) * mm) + self.space,
            y + self.space,
            boletoDados.especie)
        self.pdfCanvas.drawString(
            ((30 + 20 + 20) * mm) + self.space,
            y + self.space,
            boletoDados.quantidade or '')
        valor = self._format_value(boletoDados.valor)
        self.pdfCanvas.drawString(
            ((30 + 20 + 20 + 20 + 20) * mm) + self.space,
            y + self.space,
            valor or '')
        valorDocumento = self._format_value(boletoDados.payment.value)
        self.pdfCanvas.drawRightString(
            self.width - 2 * self.space,
            y + self.space,
            valorDocumento)
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle)

        # Linha horizontal com primeiro campo Data documento
        y += self.heightLine
        self._horizontalLine(0, y, self.width)
        self.pdfCanvas.drawString(
            0,
            y + self.deltaTitle,
            'Data do documento')
        self.pdfCanvas.drawString(
            (30 * mm) + self.space,
            y + self.deltaTitle,
            'N. do documento')
        self.pdfCanvas.drawString(
            ((30 + 40) * mm) + self.space,
            y + self.deltaTitle,
            'Esp??cie doc')
        self._verticalLine(
            (30 + 20 + 20 + 20) * mm,
            y,
            self.heightLine)
        self.pdfCanvas.drawString(
            ((30 + 40 + 20) * mm) + self.space,
            y + self.deltaTitle,
            'Aceite')
        self.pdfCanvas.drawString(
            ((30 + 40 + 40) * mm) + self.space,
            y + self.deltaTitle,
            'Data processamento')
        self.pdfCanvas.drawString(
            self.width - (45 * mm) + self.space,
            y + self.deltaTitle,
            'Nosso n??mero')

        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue)
        self.pdfCanvas.drawString(
            0,
            y + self.space,
            boletoDados.payment.open_date.strftime('%d/%m/%Y'))
        self.pdfCanvas.drawString(
            (30 * mm) + self.space,
            y + self.space,
            str(boletoDados.payment.identifier))
        self.pdfCanvas.drawString(
            ((30 + 40) * mm) + self.space,
            y + self.space,
            boletoDados.especie_documento)
        self.pdfCanvas.drawString(
            ((30 + 40 + 20) * mm) + self.space,
            y + self.space,
            boletoDados.aceite)
        self.pdfCanvas.drawString(
            ((30 + 40 + 40) * mm) + self.space,
            y + self.space,
            boletoDados.data_processamento.strftime('%d/%m/%Y'))
        self.pdfCanvas.drawRightString(
            self.width - 2 * self.space,
            y + self.space,
            boletoDados.format_nosso_numero())
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle)

        # Linha horizontal com primeiro campo Benefici??rio
        y += self.heightLine
        self._horizontalLine(0, y, self.width)
        self.pdfCanvas.drawString(0, y + self.deltaTitle, 'Benefici??rio')
        self.pdfCanvas.drawString(
            self.width - (45 * mm) + self.space,
            y + self.deltaTitle,
            'Ag??ncia/C??digo Benefici??rio')

        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue)
        self.pdfCanvas.drawString(0, y + self.space,
                                  boletoDados.branch.get_description())
        self.pdfCanvas.drawRightString(
            self.width - 2 * self.space,
            y + self.space,
            boletoDados.agencia_conta)
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle)

        # Linha horizontal com primeiro campo Local de Pagamento
        y += self.heightLine
        self._horizontalLine(0, y, self.width)
        self.pdfCanvas.drawString(
            0,
            y + self.deltaTitle,
            'Local de pagamento')
        self.pdfCanvas.drawString(
            self.width - (45 * mm) + self.space,
            y + self.deltaTitle,
            'Vencimento')

        self.pdfCanvas.setFont('Helvetica', self.fontSizeValue)
        self.pdfCanvas.drawString(
            0,
            y + self.space,
            boletoDados.local_pagamento)
        self.pdfCanvas.drawRightString(
            self.width - 2 * self.space,
            y + self.space,
            boletoDados.payment.due_date.strftime('%d/%m/%Y'))
        self.pdfCanvas.setFont('Helvetica', self.fontSizeTitle)

        # Linha grossa com primeiro campo logo tipo do banco
        self.pdfCanvas.setLineWidth(3)
        y += self.heightLine
        self._horizontalLine(0, y, self.width)
        self.pdfCanvas.setLineWidth(2)
        self._verticalLine(40 * mm, y, self.heightLine)  # Logo Tipo
        self._verticalLine(60 * mm, y, self.heightLine)  # Numero do Banco

        if boletoDados.logo_image_path:
            self.pdfCanvas.drawImage(
                boletoDados.logo_image_path,
                0,
                y + self.space + 1,
                40 * mm,
                self.heightLine,
                preserveAspectRatio=True,
                anchor='sw')
        self.pdfCanvas.setFont('Helvetica-Bold', 18)
        self.pdfCanvas.drawCentredString(
            50 * mm,
            y + 2 * self.space,
            boletoDados.codigo_dv_banco)
        self.pdfCanvas.setFont('Helvetica-Bold', 10)
        self.pdfCanvas.drawRightString(
            self.width,
            y + 2 * self.space,
            boletoDados.linha_digitavel)

        # Codigo de barras
        self._codigoBarraI25(boletoDados.barcode, 2 * self.space, 0)

        self.pdfCanvas.restoreState()

        return self.width, (y + self.heightLine) / mm

    def drawBoletoCarneDuplo(self, boletoDados1, boletoDados2):
        if self.format == self.FORMAT_CARNE:
            y = 25
        else:
            y = 5

        d = self.drawBoletoCarne(boletoDados1, y)
        y += d[1] + 6
        # self.drawHorizontalCorteLine(0, y, d[0])
        y += 7
        if boletoDados2:
            self.drawBoletoCarne(boletoDados2, y)

    def drawBoletoCarne(self, boletoDados, y):
        x = 5
        d = self.drawReciboSacadoCanhoto(boletoDados, x, y)
        x += d[0] + 6
        self.drawVerticalCorteLine(x, y, d[1])
        x += 6
        d = self.drawReciboCaixa(boletoDados, x, y)
        x += d[0]
        return x, d[1]

    def drawBoleto(self, boletoDados):
        x = 5
        y = 40
        self.drawHorizontalCorteLine(x, y, self.width / mm)
        y += 5
        d = self.drawReciboCaixa(boletoDados, x, y)
        y += d[1] + 10
        self.drawHorizontalCorteLine(x, y, self.width / mm)
        y += 10
        d = self.drawReciboSacado(boletoDados, x, y)
        return self.width, y

    def nextPage(self):
        self.pdfCanvas.showPage()

    def save(self):
        self.pdfCanvas.save()

    def add_data(self, data):
        self.boletos.append(data)

    def render(self):
        try:
            self._render_bill()
        except (BoletoException, ValueError):
            exc = sys.exc_info()
            tb_str = ''.join(traceback.format_exception(*exc))
            collect_traceback(exc, submit=True)
            raise ReportError(tb_str)

    #
    #   Private API
    #

    def _render_bill(self):
        if self.format == self.FORMAT_BOLETO:
            for b in self.boletos:
                self.drawBoleto(b)
                self.nextPage()
        elif self.format == self.FORMAT_CARNE:
            for i in range(0, len(self.boletos), 2):
                args = [self.boletos[i], None]
                if i + 1 < len(self.boletos):
                    args[1] = self.boletos[i + 1]
                self.drawBoletoCarneDuplo(*args)
                self.nextPage()

    def _horizontalLine(self, x, y, width):
        self.pdfCanvas.line(x, y, x + width, y)

    def _verticalLine(self, x, y, width):
        self.pdfCanvas.line(x, y, x, y + width)

    def _centreText(self, x, y, text):
        self.pdfCanvas.drawCentredString(self.refX + x, self.refY + y, text)

    def _rightText(self, x, y, text):
        self.pdfCanvas.drawRightString(self.refX + x, self.refY + y, text)

    def _format_value(self, value):
        if value is not None:
            txt = "%.2f" % value
            txt = txt.replace('.', ',')
        else:
            txt = ""
        return txt

    def _codigoBarraI25(self, num, x, y):
        # http://en.wikipedia.org/wiki/Interleaved_2_of_5

        altura = 13 * mm
        comprimento = 103 * mm

        tracoFino = 0.254320987654 * mm  # Tamanho correto aproximado

        bc = I2of5(num,
                   barWidth=tracoFino,
                   ratio=3,
                   barHeight=altura,
                   bearers=0,
                   quiet=0,
                   checksum=0)

        # Recalcula o tamanho do tracoFino para que o cod de barras tenha o
        # comprimento correto
        tracoFino = (tracoFino * comprimento) / bc.width
        bc.__init__(num, barWidth=tracoFino)

        bc.drawOn(self.pdfCanvas, x, y)


class BillReport(object):
    title = _('Bill')

    def __init__(self, filename, payments):
        self._payments = payments
        self._filename = filename
        self._bill = self._get_bill()

    @classmethod
    def check_printable(cls, payments):
        for payment in payments:
            msg = cls.validate_payment_for_printing(payment)
            if msg:
                warning(_("Could not print Bill Report"),
                        description=msg)
                return False

        return True

    @classmethod
    def validate_payment_for_printing(cls, payment):
        account = payment.method.destination_account
        if not account:
            msg = _("Payment method missing a destination account: '%s'") % (
                account.description, )
            return msg

        from stoqlib.domain.account import Account
        if (account.account_type != Account.TYPE_BANK or
                not account.bank):
            msg = _("Account '%s' must be a bank account.\n"
                    "You need to configure the bill payment method in "
                    "the admin application and try again") % account.description
            return msg

        bank = account.bank
        if bank.bank_number == 0:
            msg = _("Improperly configured bank account: %r") % (bank, )
            return msg

        # FIXME: Verify that all bill option fields are configured properly

        bank_no = bank.bank_number
        bank_info = get_bank_info_by_number(bank_no)
        if not bank_info:
            msg = _("Missing stoq support for bank %d") % (bank_no, )
            return msg

    def _get_bill(self):
        format = BoletoPDF.FORMAT_BOLETO
        if len(self._payments) > 1:
            format = BoletoPDF.FORMAT_CARNE
            # This is a PrintOperationPoppler's workaround to really print
            # the page in landscape, without cutting the edges
            self.print_as_landscape = True
        return BoletoPDF(self._filename, format)

    def add_payments(self):
        if self._bill.boletos:
            return

        for p in self._payments:
            if p.method.method_name != 'bill':
                continue
            account = p.method.destination_account
            _render_class = get_bank_info_by_number(account.bank.bank_number)
            data = _render_class(p)
            self._bill.add_data(data)

    def save(self):
        self.add_payments()
        self._bill.render()
        self._bill.save()


class BillTestReport(object):
    def __init__(self, filename, data):
        self.title = _("Bill")
        self._bill = BoletoPDF(filename, BoletoPDF.FORMAT_BOLETO)
        self._bill.add_data(data)

    def save(self):
        self._bill.render()
        self._bill.save()
