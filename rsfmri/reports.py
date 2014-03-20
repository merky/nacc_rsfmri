#!/usr/bin/python

import os
from jinja2 import Environment, FileSystemLoader

# Generic report
class FCReportBase(object):
    def __init__(self, label, template_file):
        reportsdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
        env = Environment(loader=FileSystemLoader(reportsdir))
        self.template = env.get_template(template_file)
        self.label = label

    def _render(self, **kwargs):
        html = self.template.render(label=self.label, **kwargs)
        return html


# renders html for seed-specific images/stats
class FCReportGroupSeeds(FCReportBase):
    def __init__(self):
        super(self.__class__, self).__init__('Seeds', 'seeds.html')
        self.seeds = {}

    def add_img(self, seed, src, label):
        self.init_seed(seed)
        self.seeds[seed].append({'type': 'image', 'src': src, 'label': label})

    def add_txt(self, seed, text):
        self.init_seed(seed)
        self.seeds[seed].append({'type': 'text', 'text': text})

    def render(self):
        return super(self.__class__,self)._render(seeds=self.seeds)

    def init_seed(self, seed):
        if not seed in self.seeds:
            self.seeds[seed] = []


# renders html for summary images/stats
class FCReportGroupSummary(FCReportBase):
    def __init__(self):
        super(self.__class__, self).__init__('Group-level Summary', 'summary.html')
        self.items = []

    def add_img(self, src, label):
        self.items.append({'type': 'image', 'src': src, 'label': label})

    def add_txt(self, text):
        self.items.append({'type': 'text', 'text': text})

    def render(self):
        return super(self.__class__,self)._render(items=self.items)


# renders combined html of all reports
class FCReport(FCReportBase):
    def __init__(self, title):
        super(self.__class__, self).__init__(title, 'report.html')
        self.reports = []

    def add_report(self, report):
        self.reports.append(report)

    def render(self):
        reports = [x.render() for x in self.reports]
        return super(self.__class__,self)._render(reports=reports)

    def render_to_file(self, filename):
        html = self.render()
        # save the results
        with open(filename, "wb") as fh: fh.write(html)

