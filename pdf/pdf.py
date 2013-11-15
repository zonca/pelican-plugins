# -*- coding: utf-8 -*-
'''
PDF Generator
-------

The pdf plugin generates PDF files from RST sources.
'''

from __future__ import unicode_literals, print_function

from pelican import signals
from pelican.generators import Generator
from rst2pdf.createpdf import RstToPdf

import os
import logging

logger = logging.getLogger(__name__)

### figshare
import requests
from requests_oauthlib import OAuth1
import json

class PdfGenerator(Generator):
    """Generate PDFs on the output dir, for all articles and pages coming from
    rst"""
    def __init__(self, *args, **kwargs):
        super(PdfGenerator, self).__init__(*args, **kwargs)
        
        pdf_style_path = os.path.join(self.settings['PDF_STYLE_PATH'])
        pdf_style = self.settings['PDF_STYLE']
        self.pdfcreator = RstToPdf(breakside=0,
                                   stylesheets=[pdf_style],
                                   style_path=[pdf_style_path],
                                   def_dpi=100)

    def _create_pdf(self, obj, output_path):
        if obj.source_path.endswith('.rst'):
            filename = obj.slug + ".pdf"
            output_pdf = os.path.join(output_path, filename)
            print('Generating pdf for', obj.source_path, 'in', output_pdf)
            with open(obj.source_path) as f:
                self.pdfcreator.createPdf(text=f.read(), output=output_pdf)
            logger.info(' [ok] writing %s' % output_pdf)

    def _upload_figshare(self, obj, output_path):
        if obj.source_path.endswith('.rst'):
            filename = obj.slug + ".pdf"
            output_pdf = os.path.join(output_path, filename)
            client_key = '8BeN60jNpgmgIN6G8oaCXQ'
            client_secret = 'oSj6EZkWChEifWOADJcKUw'
            token_key = 'sZegoc5oOgPsXfeATZGvRggVLkqc9lrYFCI9pYvDWkZAsZegoc5oOgPsXfeATZGvRg'
            token_secret = 'fifOafUWFAFcKxN6ZO9fbg'
            oauth = OAuth1(client_key=client_key, client_secret=client_secret,
                           resource_owner_key=token_key, resource_owner_secret=token_secret,
                                          signature_type = 'auth_header')
            client = requests.session()
            body = {'title':obj.title, 'description':obj.summary,'defined_type':'dataset'}
            headers = {'content-type':'application/json'}

            #response = client.post('http://api.figshare.com/v1/my_data/articles', auth=oauth, data=json.dumps(body), headers=headers)

            #results = json.loads(response.content)
            #print(results["doi"])
            #article_id = results["article_id"]
            article_id = 852126

            body = {'category_id':77} # applied computer science
            headers = {'content-type':'application/json'}
            response = client.put('http://api.figshare.com/v1/my_data/articles/%d/categories' % article_id, auth=oauth,
                                    data=json.dumps(body), headers=headers)
            results = json.loads(response.content)

            body = {'tag_name':'proceedings'}
            headers = {'content-type':'application/json'}
            response = client.put('http://api.figshare.com/v1/my_data/articles/%d/tags' % article_id, auth=oauth,
                                    data=json.dumps(body), headers=headers)
            results = json.loads(response.content)
            authors = [author.strip() for author in obj.author.name.split(",")]
            for author in authors:
                print(author)

                response = client.get('http://api.figshare.com/v1/my_data/authors?search_for=Kapil Arya', auth=oauth)
                results = json.loads(response.content)
                print(results)

                if results["results"] == 0:
                    body = {'full_name':author}
                    headers = {'content-type':'application/json'}
                    response = client.post('http://api.figshare.com/v1/my_data/authors', auth=oauth,
                                            data=json.dumps(body), headers=headers)
                    results = json.loads(response.content)
                    print(results)

                body = {'author_id':results["author_id"]}
                headers = {'content-type':'application/json'}

                response = client.put('http://api.figshare.com/v1/my_data/articles/%d/authors' % article_id, auth=oauth,
                                        data=json.dumps(body), headers=headers)
                results = json.loads(response.content)

                files = {'filedata':(os.path.basename(output_pdf), open(output_pdf, 'rb'))}

                response = client.put('http://api.figshare.com/v1/my_data/articles/%d/files' % article_id, auth=oauth,
                                      files=files)
                results = json.loads(response.content)
                print(results)
                #response = client.post('http://api.figshare.com/v1/my_data/articles/%d/action/make_public' % article_id, auth=oauth)
                #results = json.loads(response.content)

    def generate_context(self):
        pass

    def generate_output(self, writer=None):
        # we don't use the writer passed as argument here
        # since we write our own files
        logger.info(' Generating PDF files...')
        pdf_path = os.path.join(self.output_path, 'pdf')
        if not os.path.exists(pdf_path):
            try:
                os.mkdir(pdf_path)
            except OSError:
                logger.error("Couldn't create the pdf output folder in " +
                             pdf_path)

        for article in self.context['articles']:
            self._create_pdf(article, pdf_path)
            self._upload_figshare(article, pdf_path)

        for page in self.context['pages']:
            self._create_pdf(page, pdf_path)


def get_generators(generators):
    return PdfGenerator


def register():
    signals.get_generators.connect(get_generators)
