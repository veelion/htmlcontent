#!/usr/bin/env python
#coding:utf8

import re
import lxml.html
from lxml.html import HtmlComment

class Extractor(object):
    def __init__(self,):
        self.non_content_tag = set([
            'script','embed', 'iframe',
            'style',
        ])
        pass

    def get_encoding(self, html):
        r = r'charset=["\']?([\d\w\-]*)["\' />]?'
        m = re.search(r, html, re.I)
        if m:
            return m.groups()[0].lower()
        #TODO: detect charset using chardet
        return 'utf-8'

    def get_text(self, doc, is_parent=False):
        lines_element = []
        if is_parent:
            # is 'doc' is content-element's parent,
            # content-lines is its grandchildren
            ch = doc.getchildren()
            for c in ch:
                grandchildren = c.getchildren()
                if grandchildren:
                    lines_element.extend(grandchildren)
                else:
                    lines_element.append(c)
        else:
            lines_element = doc.getchildren()
        lines = []
        for el in lines_element:
            line = ''
            if el.text:
                line += el.text.strip()
            for ch in el.iter():
                if ch.text:
                    line += ch.text.strip()
            if line:
                lines.append(line)
        return '\n'.join(lines).encode('utf8')

    def get_content(self, html, just_content=True, with_tag=True):
        encoding = self.get_encoding(html)
        if encoding not in ['utf-8', 'utf8']:
            html = html.decode(encoding, 'ignore')
        doc = lxml.html.fromstring(html)

        body = doc.xpath('//body')
        if not body:
            body = doc
        else:
            body = body[0]
        elements = [body]
        last_max_len = 0
        good_el = None
        while elements:
            p = elements.pop(0)
            tlen = 0
            for el in p.iterchildren():
                if (el.tag in self.non_content_tag or
                    isinstance(el, HtmlComment)):
                    el.clear()
                    el.drop_tree()
                    continue
                elements.append(el)
                t = el.text
                if not t: continue
                t = t.strip()
                if len(t)  > 0:
                    tlen += len(t)
            if tlen < 10:
                #print 'appending candidate:', tlen
                #candidates.append((tlen, p))
                continue
            if last_max_len and tlen > 50*last_max_len:
                print 'break at: ', last_max_len, tlen
                last_max_len = tlen
                good_el = p
                break
            if last_max_len < tlen:
                last_max_len = tlen
                good_el = p
        if good_el is None:
            print 'no good_el'
            return ''
        if just_content:
            if with_tag:
                return lxml.html.tostring(good_el, encoding="utf8")
            else:
                return self.get_text(good_el)

        ## clean the content element's parent
        p = good_el.getparent()
        already_has_good = False
        for el in p.iterchildren():
            if el == good_el:
                already_has_good = True
                continue
            if el.tag in self.non_content_tag or isinstance(el, HtmlComment):
                el.clear()
                el.drop_tree()
                continue
            if not el.text:
                print 'drop tag:', el.tag
                el.clear()
                el.drop_tree()
                continue
            t = el.text.strip()
            if not t or already_has_good:
                print 'zero text drop tag:', el.tag
                el.clear()
                el.drop_tree()

        if with_tag:
            return lxml.html.tostring(p, encoding="utf8")
        else:
            return self.get_text(p, is_parent=True)





if __name__ == '__main__':
    from sys import argv, exit
    if len(argv) != 2:
        print 'usage: %s html-file' % argv[0]
        exit(-1)

    f = argv[1]
    html = open(f).read()
    ext = Extractor()
    import time
    b = time.time()
    content = ext.get_content(html, False, with_tag=True)
    e = time.time()
    print 'time cost: ', e-b
    open(f+'-content.html','w').write(content)
